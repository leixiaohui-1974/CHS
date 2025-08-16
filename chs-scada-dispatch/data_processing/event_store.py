import os
import logging
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import List, Dict, Any, Optional

class EventStore:
    """
    Manages the storage and retrieval of alarm and system events in InfluxDB.
    """
    def __init__(self):
        """
        Initializes the InfluxDB client for the events bucket.
        """
        self.url = os.getenv("INFLUXDB_URL")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG")
        # Use a separate bucket for events, defined in the environment
        self.bucket = os.getenv("INFLUXDB_EVENTS_BUCKET", "scada-events") # Default value for safety

        if not all([self.url, self.token, self.org, self.bucket]):
            raise ValueError("InfluxDB credentials (URL, TOKEN, ORG, EVENTS_BUCKET) not set in environment variables.")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logging.info(f"Successfully connected to InfluxDB for EventStore at {self.url} (bucket: {self.bucket})")
        except Exception as e:
            logging.error(f"Failed to connect to InfluxDB for EventStore: {e}")
            raise

    def add_event(self, event_data: Dict[str, Any]):
        """
        Writes an event (alarm or system event) to the InfluxDB events bucket.
        """
        try:
            timestamp = event_data.get("timestamp", datetime.utcnow().isoformat() + "Z")

            point = Point("event") \
                .time(timestamp) \
                .tag("type", event_data.get("type")) \
                .tag("source", event_data.get("source")) \
                .tag("severity", event_data.get("severity")) \
                .tag("status", event_data.get("status")) \
                .field("message", event_data.get("message", "")) \
                .field("rule_name", event_data.get("rule_name", "")) # Add other relevant fields

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logging.info(f"Successfully wrote event from source {event_data.get('source')} to event store.")
        except Exception as e:
            logging.error(f"Error writing event to InfluxDB: {e}")

    def get_events(self, filter_status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves a list of events, with optional filtering by status.
        """
        events = []
        try:
            # Base query
            flux_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d) // Look back 30 days, adjust as needed
              |> filter(fn: (r) => r["_measurement"] == "event")
            '''

            # Add filter if provided
            if filter_status and filter_status.lower() != 'all':
                flux_query += f' |> filter(fn: (r) => r["status"] == "{filter_status.upper()}")'

            # Add sorting and limit
            flux_query += f'''
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: {limit})
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

            tables = self.query_api.query(flux_query, org=self.org)

            for table in tables:
                for record in table.records:
                    event_record = {
                        "timestamp": record.get_time().isoformat(),
                        "type": record.values.get('type'),
                        "source": record.values.get('source'),
                        "severity": record.values.get('severity'),
                        "status": record.values.get('status'),
                        "message": record.values.get('message'),
                        "rule_name": record.values.get('rule_name')
                    }
                    events.append(event_record)

            logging.info(f"Retrieved {len(events)} events from the event store.")
            return events
        except Exception as e:
            logging.error(f"Error querying events from InfluxDB: {e}")
            return []

    def close(self):
        """
        Closes the InfluxDB client connection.
        """
        self.client.close()
        logging.info("EventStore InfluxDB client closed.")
