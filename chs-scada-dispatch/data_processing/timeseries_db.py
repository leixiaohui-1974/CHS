import os
import logging
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict, Any, List, Optional

class TimeSeriesDB:
    """
    Manages all interactions with the InfluxDB time-series database.
    """
    def __init__(self):
        """
        Initializes the InfluxDB client using credentials from environment variables.
        """
        self.url = os.getenv("INFLUXDB_URL")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG")
        self.bucket = os.getenv("INFLUXDB_BUCKET")

        if not all([self.url, self.token, self.org, self.bucket]):
            raise ValueError("InfluxDB credentials (URL, TOKEN, ORG, BUCKET) not set in environment variables.")

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logging.info(f"Successfully connected to InfluxDB at {self.url}")
        except Exception as e:
            logging.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def write_device_status(self, device_id: str, data: Dict[str, Any]):
        """
        Writes a device status data point to InfluxDB.
        The data payload is expected to contain 'timestamp' and 'values'.
        """
        try:
            timestamp = data.get("timestamp", datetime.utcnow().isoformat())
            values = data.get("values", {})

            point = Point("device_status") \
                .tag("device_id", device_id) \
                .time(timestamp)

            for key, value in values.items():
                if isinstance(value, (int, float, bool, str)):
                    point = point.field(key, value)
                else:
                    logging.warning(f"Skipping non-primitive field '{key}' for InfluxDB write.")

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logging.info(f"Successfully wrote status for device {device_id} to InfluxDB.")
        except Exception as e:
            logging.error(f"Error writing to InfluxDB for device {device_id}: {e}")

    def get_latest_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves the latest status for all devices from InfluxDB.
        """
        statuses = {}
        try:
            flux_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "device_status")
              |> group(by: ["device_id"])
              |> last()
            '''
            tables = self.query_api.query(flux_query, org=self.org)

            # Process the query result into a more usable format
            for table in tables:
                for record in table.records:
                    device_id = record.values.get('device_id')
                    if device_id not in statuses:
                        statuses[device_id] = {"values": {}}

                    statuses[device_id]["values"][record.get_field()] = record.get_value()
                    statuses[device_id]["timestamp"] = record.get_time().isoformat()

            logging.info(f"Retrieved latest status for {len(statuses)} devices.")
            return statuses
        except Exception as e:
            logging.error(f"Error querying latest statuses from InfluxDB: {e}")
            return {}

    def get_historical_status(self, device_id: str, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Retrieves historical status data for a specific device within a time range.
        """
        history = []
        try:
            flux_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start}, stop: {end})
              |> filter(fn: (r) => r["_measurement"] == "device_status" and r["device_id"] == "{device_id}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            tables = self.query_api.query(flux_query, org=self.org)

            for table in tables:
                for record in table.records:
                    point_in_time = {"timestamp": record.get_time().isoformat()}
                    point_in_time.update(record.values)
                    history.append(point_in_time)

            logging.info(f"Retrieved {len(history)} historical points for device {device_id}.")
            return history
        except Exception as e:
            logging.error(f"Error querying historical status for device {device_id}: {e}")
            return []

    def close(self):
        """
        Closes the InfluxDB client connection.
        """
        self.client.close()
        logging.info("InfluxDB client closed.")
