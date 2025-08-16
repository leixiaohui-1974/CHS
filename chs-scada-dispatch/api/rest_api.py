from flask import Flask, jsonify
from data_processing.status_store import StatusStore
import logging

def create_app(status_store: StatusStore):
    """
    Creates and configures the Flask application.
    Injects the status_store to make the app testable and modular.
    """
    app = Flask(__name__)

    # Configure logging to be compatible with the rest of the application
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    @app.route('/api/v1/system_status', methods=['GET'])
    def get_system_status():
        """
        API endpoint to get the current status of all systems.
        It retrieves the data from the injected status_store.
        """
        try:
            statuses = status_store.get_all_statuses()
            logging.info(f"API call to /api/v1/system_status returned status for {len(statuses)} devices.")
            return jsonify(statuses)
        except Exception as e:
            logging.error(f"An error occurred while handling /api/v1/system_status: {e}")
            # Return a generic error message to the client
            return jsonify({"error": "An internal server error occurred"}), 500

    return app
