import logging
from flask_socketio import SocketIO, emit

socketio = SocketIO()

def init_socketio(app):
    """
    Initializes the SocketIO server with the Flask app.
    """
    socketio.init_app(app, cors_allowed_origins="*")
    logging.info("Flask-SocketIO initialized.")
    return socketio

@socketio.on('connect')
def handle_connect():
    """
    Handles a new client connection.
    """
    logging.info("HMI client connected.")
    emit('confirmation', {'message': 'Successfully connected to CHS-SCADA-Dispatch WebSocket.'})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handles a client disconnection.
    """
    logging.info("HMI client disconnected.")

@socketio.on('decision_response')
def handle_decision_response(data):
    """
    Listens for a decision response from an HMI client.
    This would be passed back to the CentralExecutor.
    """
    logging.info(f"Received decision_response from HMI: {data}")
    # In a full implementation, this would trigger an event or callback
    # to pass the data back to the CentralExecutor who initiated the request.
    # For now, we just acknowledge it.
    emit('response_acknowledged', {'request_id': data.get('request_id')})

def broadcast_decision_request(request_data):
    """
    Broadcasts a request for a human decision to all connected HMI clients.
    """
    logging.info(f"Broadcasting decision_request to all HMI clients: {request_data}")
    socketio.emit('decision_request', request_data)
