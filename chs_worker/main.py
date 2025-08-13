import pika
import json
import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Add the SDK to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from water_system_sdk.src.water_system_simulator.simulation_manager import SimulationManager

# --- Health Check Server ---
HEALTH_PORT = 8080

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_health_check_server():
    server = HTTPServer(('', HEALTH_PORT), HealthCheckHandler)
    print(f"Health check server started on port {HEALTH_PORT}")
    server.serve_forever()

# --- RabbitMQ Worker ---
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
TASK_QUEUE = "simulation_tasks"
MAX_RETRIES = 10
RETRY_DELAY = 5

def run_simulation_from_message(body):
    print(" [x] Received simulation task")
    try:
        config = json.loads(body)
        print("     - Configuration parsed successfully.")
        manager = SimulationManager(config=config)
        print("     - SimulationManager initialized.")
        results_df = manager.run()
        print("     - Simulation finished successfully.")
        print("     - Result summary:")
        print(results_df.describe())
    except Exception as e:
        print(f" [!] An unexpected error occurred during simulation: {e}")

def main():
    # Start health check server in a daemon thread
    health_thread = threading.Thread(target=start_health_check_server, daemon=True)
    health_thread.start()

    # Connect to RabbitMQ with retries
    connection = None
    for i in range(MAX_RETRIES):
        try:
            print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}... (Attempt {i+1}/{MAX_RETRIES})")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            print("Successfully connected to RabbitMQ.")
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"Connection failed. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

    if not connection:
        print("Could not connect to RabbitMQ. Exiting.")
        sys.exit(1)

    channel = connection.channel()
    channel.queue_declare(queue=TASK_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        run_simulation_from_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=TASK_QUEUE, on_message_callback=callback)

    print(f" [*] Waiting for messages on queue '{TASK_QUEUE}'. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Interrupted. Shutting down.")
        connection.close()
        sys.exit(0)

if __name__ == '__main__':
    main()
