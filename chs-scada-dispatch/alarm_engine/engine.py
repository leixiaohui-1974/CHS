import logging
import time
import threading
import yaml
import os
from fnmatch import fnmatch
from datetime import datetime
from typing import List, Dict, Any

from data_processing.timeseries_db import TimeSeriesDB
from data_processing.event_store import EventStore


class AlarmEngine:
    """
    Periodically checks device statuses against a set of rules and generates alarms.
    """

    def __init__(self, timeseries_db: TimeSeriesDB, event_store: EventStore):
        self.timeseries_db = timeseries_db
        self.event_store = event_store
        self.rules = self._load_rules()
        self.is_running = False
        self.thread = None
        self.check_interval_sec = 10
        # Keep track of active alarms to avoid spamming
        # Key: (rule_name, device_id), Value: last alarm timestamp
        self._active_alarms = {}

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Loads alarm rules from the YAML file."""
        # Correct path relative to the project root
        rules_path = os.path.join(os.path.dirname(__file__), 'rules.yaml')
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
                logging.info(f"Successfully loaded {len(rules)} alarm rules from {rules_path}")
                return rules
        except FileNotFoundError:
            logging.error(f"Alarm rules file not found at {rules_path}. No alarms will be generated.")
            return []
        except Exception as e:
            logging.error(f"Error loading or parsing alarm rules: {e}")
            return []

    def _evaluate_condition(self, condition: str, device_status: Dict[str, Any]) -> bool:
        """
        Safely evaluates a rule's condition string against a device's status.
        'values' is a dictionary available in the local scope of the evaluation.
        """
        try:
            # The 'values' dict from the device status is made available to the eval context
            return eval(condition, {"__builtins__": {}}, {"values": device_status.get("values", {})})
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition}': {e}", exc_info=False)
            return False

    def run_check_cycle(self):
        """The main loop for the alarm engine."""
        while self.is_running:
            logging.info("Running alarm check cycle...")
            try:
                device_statuses = self.timeseries_db.get_latest_statuses()
                if not device_statuses:
                    logging.warning("No device statuses received from DB. Skipping alarm check.")
                else:
                    self._check_all_devices(device_statuses)
            except Exception as e:
                logging.error(f"An unexpected error occurred in the alarm check cycle: {e}", exc_info=True)

            time.sleep(self.check_interval_sec)

    def _check_all_devices(self, device_statuses: Dict[str, Dict[str, Any]]):
        """Iterates through all devices and their statuses, checking against rules."""
        for device_id, status in device_statuses.items():
            for rule in self.rules:
                # Check if the rule applies to this device using glob-style matching
                if fnmatch(device_id, rule['device_id_pattern']):
                    self._check_rule_for_device(rule, device_id, status)

    def _check_rule_for_device(self, rule: Dict[str, Any], device_id: str, status: Dict[str, Any]):
        """Checks a single rule for a single device and creates an alarm if triggered."""
        alarm_key = (rule['rule_name'], device_id)
        is_triggered = self._evaluate_condition(rule['condition'], status)

        if is_triggered:
            # Prevent re-triggering an alarm that is already active
            if alarm_key in self._active_alarms:
                logging.debug(f"Alarm {alarm_key} is already active. Skipping.")
                return

            logging.warning(f"ALARM TRIGGERED: Rule '{rule['rule_name']}' for device '{device_id}'")
            self._active_alarms[alarm_key] = datetime.utcnow()

            # Format the message with device-specific values
            message = rule['message'].format(device_id=device_id, values=status.get("values", {}))

            alarm_event = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "type": "ALARM",
                "severity": rule['severity'],
                "source": device_id,
                "message": message,
                "status": "ACTIVE",
                "rule_name": rule['rule_name']
            }
            # This will be implemented in the next step
            if self.event_store:
                self.event_store.add_event(alarm_event)

        else:
            # If the condition is no longer met, the alarm can be considered resolved
            if alarm_key in self._active_alarms:
                logging.info(f"ALARM RESOLVED: Rule '{rule['rule_name']}' for device '{device_id}'")
                # Here you could update the event status to 'RESOLVED'
                # For now, we just remove it from the active list to allow re-triggering
                del self._active_alarms[alarm_key]


    def start(self):
        """Starts the alarm engine's check cycle in a background thread."""
        if self.is_running:
            logging.warning("Alarm engine is already running.")
            return
        if not self.rules:
            logging.warning("No rules loaded. Alarm engine will not start.")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self.run_check_cycle, daemon=True)
        self.thread.start()
        logging.info("Alarm Engine started.")

    def stop(self):
        """Stops the alarm engine."""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            logging.info("Alarm Engine stopped.")
