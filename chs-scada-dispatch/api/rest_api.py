from flask import Flask, jsonify, request
from data_processing.timeseries_db import TimeSeriesDB
from data_processing.event_store import EventStore
from data_ingestion.mqtt_service import MqttService
import logging
from datetime import datetime, timedelta

def create_rest_app(timeseries_db: TimeSeriesDB, event_store: EventStore, mqtt_service: MqttService):
    """
    Creates and configures the Flask application for RESTful APIs.
    Injects dependencies to make the app modular and testable.
    """
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    @app.route('/api/v1/system_status', methods=['GET'])
    def get_system_status():
        """
        API endpoint to get the current status of all systems from InfluxDB.
        """
        try:
            statuses = timeseries_db.get_latest_statuses()
            logging.info(f"API call to /api/v1/system_status returned status for {len(statuses)} devices.")
            return jsonify(statuses)
        except Exception as e:
            logging.error(f"Error in /api/v1/system_status: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/command', methods=['POST'])
    def post_command():
        """
        API endpoint to manually issue a command to a device.
        """
        try:
            data = request.get_json()
            if not data or 'target_device_id' not in data or 'command' not in data:
                return jsonify({"error": "Invalid request body. 'target_device_id' and 'command' are required."}), 400

            device_id = data['target_device_id']
            command = data['command']

            logging.info(f"Received API request to issue command to {device_id}: {command}")
            mqtt_service.publish_command(device_id, command)

            return jsonify({"message": "Command successfully sent to the queue."}), 202
        except Exception as e:
            logging.error(f"Error in /api/v1/command: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/events', methods=['GET'])
    def get_events():
        """
        API endpoint to get the list of alarms and system events.
        """
        try:
            # Get query parameters
            filter_status = request.args.get('filter', default='all', type=str)
            limit = request.args.get('limit', default=100, type=int)

            events = event_store.get_events(filter_status=filter_status, limit=limit)
            logging.info(f"API call to /api/v1/events with filter='{filter_status}' returned {len(events)} events.")
            return jsonify(events)
        except Exception as e:
            logging.error(f"Error in /api/v1/events: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/devices/<string:device_id>/history', methods=['GET'])
    def get_device_history(device_id):
        """
        API endpoint to get historical data for a specific device.
        """
        try:
            # Get and parse query parameters
            time_range_str = request.args.get('range', default='1h', type=str)

            # Simple parser for range string like '1h', '24h', '7d'
            # Note: In a real production system, this would be more robust.
            if time_range_str.endswith('h'):
                hours = int(time_range_str[:-1])
                delta = timedelta(hours=hours)
            elif time_range_str.endswith('d'):
                days = int(time_range_str[:-1])
                delta = timedelta(days=days)
            else: # Default to 1 hour if format is unrecognized
                delta = timedelta(hours=1)

            # The `get_historical_status` method expects a relative time string (e.g., "-1h")
            # or an absolute timestamp. We can simplify this by passing the relative time string directly.
            # The 'end' parameter is optional in the DB layer method.

            # The field parameter is not used yet, but could be in the future
            # field = request.args.get('field', type=str)

            history = timeseries_db.get_historical_status(device_id, start=f"-{time_range_str}", end="now()")
            logging.info(f"API call to /api/v1/devices/{device_id}/history with range='{time_range_str}' returned {len(history)} points.")
            return jsonify(history)
        except Exception as e:
            logging.error(f"Error in /api/v1/devices/{device_id}/history: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    return app
