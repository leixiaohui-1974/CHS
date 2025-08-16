import os
import logging
import uuid
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.delete_api import DeleteApi
from typing import List, Dict, Any, Optional

class EventStore:
    """
    Manages the storage and retrieval of alarm and system events in InfluxDB.
    Events are designed to be stateful, with a unique ID allowing for updates.
    """
    def __init__(self):
        """
        Initializes the InfluxDB client for the events bucket.
        """
        self.url = os.getenv("INFLUXDB_URL")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG")
        self.bucket = os.getenv("INFLUXDB_EVENTS_BUCKET", "scada-events")

        if not all([self.url, self.token, self.org, self.bucket]):
            raise ValueError("InfluxDB credentials (URL, TOKEN, ORG, EVENTS_BUCKET) not set in environment variables.")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            self.delete_api = self.client.delete_api()
            logging.info(f"Successfully connected to InfluxDB for EventStore at {self.url} (bucket: {self.bucket})")
        except Exception as e:
            logging.error(f"Failed to connect to InfluxDB for EventStore: {e}")
            raise

    def add_event(self, event_data: Dict[str, Any]):
        """
        Writes an event to the InfluxDB events bucket. If an 'event_id' is not present,
        a new one is generated. This allows for re-writing events to update them.
        """
        try:
            # Ensure event_id exists, creating one if this is a new event
            event_id = event_data.get("event_id", str(uuid.uuid4()))

            timestamp = event_data.get("timestamp", datetime.now(timezone.utc).isoformat())

            point = Point("event") \
                .time(timestamp) \
                .tag("event_id", event_id) \
                .tag("type", event_data.get("type", "SYSTEM")) \
                .tag("source", event_data.get("source", "unknown")) \
                .tag("severity", event_data.get("severity", "INFO")) \
                .tag("status", event_data.get("status", "NEW")) \
                .field("message", event_data.get("message", "")) \
                .field("rule_name", event_data.get("rule_name", "")) \
                .field("acknowledged_by", event_data.get("acknowledged_by", "")) \
                .field("resolved_by", event_data.get("resolved_by", "")) \
                .field("resolution_notes", event_data.get("resolution_notes", ""))

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logging.info(f"Successfully wrote event {event_id} from source {event_data.get('source')} to event store.")
        except Exception as e:
            logging.error(f"Error writing event to InfluxDB: {e}")

    def get_events(self, filter_status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves a list of events, with optional filtering by status.
        """
        try:
            flux_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "event")
            '''

            if filter_status and filter_status.lower() != 'all':
                flux_query += f' |> filter(fn: (r) => r["status"] == "{filter_status.upper()}")'

            flux_query += f'''
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: {limit})
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

            tables = self.query_api.query(flux_query, org=self.org)
            events = []
            for table in tables:
                for record in table.records:
                    events.append(record.values)

            logging.info(f"Retrieved {len(events)} events from the event store.")
            return events
        except Exception as e:
            logging.error(f"Error querying events from InfluxDB: {e}")
            return []

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single event by its unique event_id."""
        try:
            flux_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "event")
              |> filter(fn: (r) => r["event_id"] == "{event_id}")
              |> last()
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            tables = self.query_api.query(flux_query, org=self.org)
            if not tables or not tables[0].records:
                logging.warning(f"No event found with event_id: {event_id}")
                return None

            event_record = tables[0].records[0].values
            logging.info(f"Successfully retrieved event: {event_id}")
            return event_record
        except Exception as e:
            logging.error(f"Error querying event {event_id} from InfluxDB: {e}")
            return None

    def _delete_event(self, event_id: str):
        """Deletes an event from InfluxDB based on its event_id tag."""
        try:
            # InfluxDB's delete requires a time range. We use a wide range.
            # The predicate ensures we only delete the specific event.
            start = "1970-01-01T00:00:00Z"
            stop = datetime.now(timezone.utc).isoformat()
            predicate = f'_measurement="event" AND event_id="{event_id}"'

            self.delete_api.delete(start, stop, predicate, bucket=self.bucket, org=self.org)
            logging.info(f"Successfully submitted delete request for event: {event_id}")
        except Exception as e:
            logging.error(f"Error deleting event {event_id} from InfluxDB: {e}")
            raise

    def acknowledge_event(self, event_id: str, user: str) -> bool:
        """Acknowledges an event, marking its status as ACKNOWLEDGED."""
        event = self.get_event(event_id)
        if not event:
            return False

        # Prevent re-acknowledging
        if event.get("status") in ["ACKNOWLEDGED", "RESOLVED"]:
            logging.warning(f"Event {event_id} is already in status {event.get('status')}. No action taken.")
            return True

        self._delete_event(event_id)

        event["status"] = "ACKNOWLEDGED"
        event["acknowledged_by"] = user
        # Preserve original timestamp but update to current time if missing
        event["timestamp"] = event.get("_time", datetime.now(timezone.utc).isoformat())

        self.add_event(event)
        logging.info(f"Event {event_id} acknowledged by user {user}.")
        return True

    def resolve_event(self, event_id: str, user: str, notes: str) -> bool:
        """Resolves an event, marking its status as RESOLVED and adding notes."""
        event = self.get_event(event_id)
        if not event:
            return False

        if event.get("status") == "RESOLVED":
            logging.warning(f"Event {event_id} is already resolved. No action taken.")
            return True

        self._delete_event(event_id)

        event["status"] = "RESOLVED"
        event["resolved_by"] = user
        event["resolution_notes"] = notes
        event["timestamp"] = event.get("_time", datetime.now(timezone.utc).isoformat())

        self.add_event(event)
        logging.info(f"Event {event_id} resolved by user {user} with notes.")
        return True

    def close(self):
        """
        Closes the InfluxDB client connection.
        """
        self.client.close()
        logging.info("EventStore InfluxDB client closed.")
