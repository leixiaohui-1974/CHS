import logging
import os
import atexit
from dotenv import load_dotenv

from api.rest_api import create_rest_app
from api.websocket_api import init_socketio
from data_processing.timeseries_db import TimeSeriesDB
from data_ingestion.mqtt_service import MqttService
from dispatch_engine.central_agent_executor import CentralExecutor

# --- Global Service Instances ---
# These are managed here to ensure they are gracefully shut down on exit.
timeseries_db: TimeSeriesDB = None
mqtt_service: MqttService = None
dispatch_engine: CentralExecutor = None

def main():
    """
    Main function to initialize and run the CHS-SCADA-Dispatch application.
    """
    # 1. Load environment variables from .env file
    load_dotenv()

    # 2. Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger("werkzeug").setLevel(logging.WARNING) # Quieter Flask logs
    logging.getLogger("engineio").setLevel(logging.WARNING) # Quieter SocketIO logs

    global timeseries_db, mqtt_service, dispatch_engine

    try:
        # 3. Initialize services
        logging.info("Initializing services...")
        # InfluxDB URL and broker address can be configured via .env file
        influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        mqtt_broker = os.getenv("MQTT_BROKER_ADDRESS", "127.0.0.1")

        timeseries_db = TimeSeriesDB()
        mqtt_service = MqttService(timeseries_db=timeseries_db, broker_address=mqtt_broker)
        dispatch_engine = CentralExecutor(
            timeseries_db=timeseries_db,
            mqtt_service=mqtt_service
            # websocket_service will be set after initialization
        )
        logging.info("Core services initialized.")

        # 4. Create the Flask app and inject dependencies
        app = create_rest_app(
            timeseries_db=timeseries_db,
            mqtt_service=mqtt_service
        )

        # 5. Initialize WebSocket (SocketIO) and link it to the dispatch engine
        # This creates a circular dependency that is resolved at runtime.
        # Engine needs SocketIO to emit, SocketIO needs Engine to handle callbacks.
        socketio = init_socketio(app, engine=dispatch_engine)
        dispatch_engine.websocket_service = socketio # Provide websocket access back to engine

        logging.info("Web services initialized.")

        # 6. Register cleanup function to run on exit
        atexit.register(cleanup)

        # 7. Start background services
        logging.info("Starting background services...")
        mqtt_service.start()
        dispatch_engine.start()
        logging.info("Background services started.")

        # 8. Run the web server
        port = int(os.getenv("PORT", 5000))
        logging.info(f"Starting Flask-SocketIO server on port {port}...")
        # allow_unsafe_werkzeug=True is needed for dev server reloader with SocketIO
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

    except Exception as e:
        logging.critical(f"Application failed to start: {e}", exc_info=True)
    finally:
        # This will be called on normal shutdown if not using atexit
        cleanup()

def cleanup():
    """
    Gracefully stops all running services.
    """
    logging.info("Application is shutting down. Cleaning up resources...")
    global mqtt_service, dispatch_engine, timeseries_db

    if dispatch_engine and dispatch_engine.is_running:
        dispatch_engine.stop()
    if mqtt_service:
        mqtt_service.stop()
    if timeseries_db:
        timeseries_db.close()

    logging.info("Cleanup complete.")

if __name__ == '__main__':
    main()
