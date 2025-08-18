import { io } from 'socket.io-client';

// The backend is proxied, so we can connect to the same host.
// The namespace '/live' must match the one on the server.
const SOCKET_URL = '/live';

class LiveSimulationService {
  socket;

  connect() {
    if (this.socket && this.socket.connected) {
      return;
    }
    console.log('Connecting to live simulation service...');
    this.socket = io(SOCKET_URL, {
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log(`Connected to live simulation service with ID: ${this.socket.id}`);
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from live simulation service.');
    });

    this.socket.on('connect_error', (err) => {
        console.error('Connection error:', err.message);
    });
  }

  joinSimulation(simulationId) {
    if (this.socket) {
      console.log(`Joining simulation room: ${simulationId}`);
      this.socket.emit('join_simulation_room', { simulation_id: simulationId });
    }
  }

  onSimulationUpdate(callback) {
    if (this.socket) {
      this.socket.on('simulation_update', callback);
    }
  }

  onSimulationEnd(callback) {
    if (this.socket) {
        this.socket.on('simulation_end', callback);
    }
  }

  onSimulationError(callback) {
    if (this.socket) {
        this.socket.on('simulation_error', callback);
    }
  }

  // Method to remove listeners to prevent memory leaks in React components
  cleanupListeners() {
      if (this.socket) {
          this.socket.off('simulation_update');
          this.socket.off('simulation_end');
          this.socket.off('simulation_error');
      }
  }

  disconnect() {
    if (this.socket) {
      console.log('Disconnecting from service.');
      this.socket.disconnect();
    }
  }
}

// Export a singleton instance of the service
const liveSimulationService = new LiveSimulationService();
export default liveSimulationService;
