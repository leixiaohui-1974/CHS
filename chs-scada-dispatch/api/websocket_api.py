import logging
from flask_socketio import SocketIO, emit
from dispatch_engine.central_agent_executor import CentralExecutor

# --- Global Service Instances ---
socketio = SocketIO()
dispatch_engine: CentralExecutor = None

def init_socketio(app, engine: CentralExecutor):
    """
    Initializes the SocketIO server and links it to the dispatch engine.
    """
    global dispatch_engine
    dispatch_engine = engine

    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
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
    Listens for a decision response from an HMI client and passes it
    to the CentralExecutor.
    """
    logging.info(f"Received decision_response from HMI: {data}")
    request_id = data.get("request_id")
    decision = data.get("decision")

    if not all([request_id, isinstance(decision, dict)]):
        logging.error(f"Invalid decision_response received: {data}")
        emit('error', {'message': 'Invalid response format. Must include request_id and decision object.'})
        return

    if dispatch_engine:
        dispatch_engine.submit_human_decision(request_id, decision)
        emit('response_acknowledged', {'request_id': request_id})
    else:
        logging.error("Dispatch engine not initialized. Cannot process decision.")
        emit('error', {'message': 'Server error: Dispatch engine not available.'})
