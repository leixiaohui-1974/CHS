from flask import Flask, jsonify, request
from data_processing.timeseries_db import TimeSeriesDB
from data_processing.event_store import EventStore
from data_ingestion.mqtt_service import MqttService
from audit_log.audit_logger import AuditLogger
import logging
from datetime import datetime, timedelta

def create_rest_app(timeseries_db: TimeSeriesDB, event_store: EventStore, mqtt_service: MqttService, audit_logger: AuditLogger):
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
            if not data or 'target_device_id' not in data or 'command' not in data or 'user' not in data:
                return jsonify({"error": "Invalid request body. 'target_device_id', 'command', and 'user' are required."}), 400

            device_id = data['target_device_id']
            command = data['command']
            user = data['user']

            logging.info(f"Received API request from user '{user}' to issue command to {device_id}: {command}")

            # Audit the action
            audit_logger.log(user, 'SEND_COMMAND', {'device_id': device_id, 'command': command})

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
            filter_status = request.args.get('filter', default='all', type=str)
            limit = request.args.get('limit', default=100, type=int)

            events = event_store.get_events(filter_status=filter_status, limit=limit)
            logging.info(f"API call to /api/v1/events with filter='{filter_status}' returned {len(events)} events.")
            return jsonify(events)
        except Exception as e:
            logging.error(f"Error in /api/v1/events: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/events/<string:event_id>/ack', methods=['POST'])
    def acknowledge_event(event_id):
        """Acknowledges an alarm or event."""
        try:
            data = request.get_json()
            if not data or 'user' not in data:
                return jsonify({"error": "'user' is required in the request body."}), 400

            user = data['user']
            success = event_store.acknowledge_event(event_id, user)

            if success:
                audit_logger.log(user, 'ACKNOWLEDGE_EVENT', {'event_id': event_id})
                return jsonify({"message": f"Event {event_id} acknowledged."}), 200
            else:
                return jsonify({"error": f"Event {event_id} not found or already handled."}), 404
        except Exception as e:
            logging.error(f"Error in /api/v1/events/{event_id}/ack: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/events/<string:event_id>/resolve', methods=['POST'])
    def resolve_event(event_id):
        """Resolves an alarm or event."""
        try:
            data = request.get_json()
            if not data or 'user' not in data:
                return jsonify({"error": "'user' is required in the request body."}), 400

            user = data['user']
            notes = data.get('notes', '') # Notes are optional
            success = event_store.resolve_event(event_id, user, notes)

            if success:
                audit_logger.log(user, 'RESOLVE_EVENT', {'event_id': event_id, 'notes': notes})
                return jsonify({"message": f"Event {event_id} resolved."}), 200
            else:
                return jsonify({"error": f"Event {event_id} not found."}), 404
        except Exception as e:
            logging.error(f"Error in /api/v1/events/{event_id}/resolve: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/devices/<string:device_id>/config', methods=['POST'])
    def update_device_config(device_id):
        """Updates the configuration for a remote CHS-Edge device."""
        try:
            config_data = request.get_json()
            if not config_data:
                return jsonify({"error": "Request body must contain valid configuration JSON."}), 400

            # It's good practice to record who initiated the change.
            user = config_data.pop('user', 'unknown_user')

            mqtt_service.publish_config(device_id, config_data)
            audit_logger.log(user, 'UPDATE_DEVICE_CONFIG', {'device_id': device_id, 'config': config_data})

            return jsonify({"message": f"Configuration update sent to device {device_id}."}), 202
        except Exception as e:
            logging.error(f"Error in /api/v1/devices/{device_id}/config: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/devices/<string:device_id>/history', methods=['GET'])
    def get_device_history(device_id):
        """
        API endpoint to get historical data for a specific device.
        """
        try:
            time_range_str = request.args.get('range', default='1h', type=str)

            if time_range_str.endswith('h'):
                delta = timedelta(hours=int(time_range_str[:-1]))
            elif time_range_str.endswith('d'):
                delta = timedelta(days=int(time_range_str[:-1]))
            else:
                delta = timedelta(hours=1)

            history = timeseries_db.get_historical_status(device_id, start=f"-{time_range_str}", end="now()")
            logging.info(f"API call to /api/v1/devices/{device_id}/history with range='{time_range_str}' returned {len(history)} points.")
            return jsonify(history)
        except Exception as e:
            logging.error(f"Error in /api/v1/devices/{device_id}/history: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    return app
