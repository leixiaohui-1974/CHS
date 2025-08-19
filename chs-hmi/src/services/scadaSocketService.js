import { io } from 'socket.io-client';

// The backend is proxied, so we can connect to the same host.
// The SCADA service uses the default namespace.
const SCADA_SOCKET_URL = process.env.REACT_APP_SCADA_WEBSOCKET_URL || 'http://localhost:8001';

class ScadaSocketService {
  socket;

  connect(auth) {
    if (this.socket && this.socket.connected) {
      return;
    }
    console.log('Connecting to SCADA WebSocket service...');
    this.socket = io(SCADA_SOCKET_URL, {
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      auth: { token: auth?.token } // Pass auth token if available
    });

    this.socket.on('connect', () => {
      console.log(`Connected to SCADA service with ID: ${this.socket.id}`);
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`Disconnected from SCADA service: ${reason}`);
    });

    this.socket.on('connect_error', (err) => {
        console.error(`SCADA connection error: ${err.message}`);
    });

    this.socket.on('confirmation', (data) => {
        console.log('Connection confirmed by server:', data.message);
    });

    this.socket.on('error', (data) => {
        console.error('Received error from server:', data.message);
    });
  }

  // --- Listeners for data from the server ---

  onStatusUpdate(callback) {
    if (this.socket) {
      this.socket.on('status_update', callback);
    }
  }

  onDecisionRequest(callback) {
    if (this.socket) {
      this.socket.on('decision_request', callback);
    }
  }

  // --- Emitters for sending data to the server ---

  sendDecision(requestId, decision) {
    if (this.socket) {
      this.socket.emit('decision_response', {
        request_id: requestId,
        decision: decision
      });
    }
  }

  // --- Cleanup ---

  cleanupListeners() {
      if (this.socket) {
          this.socket.off('status_update');
          this.socket.off('decision_request');
      }
  }

  disconnect() {
    if (this.socket) {
      console.log('Disconnecting from SCADA service.');
      this.cleanupListeners();
      this.socket.disconnect();
    }
  }
}

// Export a singleton instance of the service
const scadaSocketService = new ScadaSocketService();
export default scadaSocketService;
