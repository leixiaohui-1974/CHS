/* eslint-disable no-unused-vars */
const WEBSOCKET_URL = 'ws://localhost:8080/ws'; // Adjust if your backend URL is different

class WebSocketService {
  constructor() {
    this.socket = null;
    this.decisionRequestCallback = null;
  }

  connect(decisionRequestCallback) {
    this.decisionRequestCallback = decisionRequestCallback;

    // Ensure we don't create duplicate connections
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket is already connected.');
      return;
    }

    this.socket = new WebSocket(WEBSOCKET_URL);

    // Expose the socket instance for testing purposes
    if (process.env.NODE_ENV === 'development') {
      window.webSocketInstance = this.socket;
    }

    this.socket.onopen = () => {
      console.log('WebSocket connection established.');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);

        if (data.event === 'decision_request' && this.decisionRequestCallback) {
          this.decisionRequestCallback(data);
        }
        // Here you could handle other event types, like 'status_update'

      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket connection closed:', event);
      // Optional: implement reconnection logic here
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  sendDecision(deviceId, action) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected.');
      return;
    }

    const message = {
      event: 'decision_response',
      device_id: deviceId,
      action: action,
    };

    this.socket.send(JSON.stringify(message));
    console.log('Sent decision:', message);
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}

// Export a singleton instance
const websocketService = new WebSocketService();
export default websocketService;
