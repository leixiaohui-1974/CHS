import logging
import json
from datetime import datetime

class AuditLogger:
    """
    Handles logging of critical system and user actions to an audit trail.
    """
    def __init__(self, log_file_path="audit.log"):
        """
        Initializes the logger.

        Args:
            log_file_path (str): The path to the audit log file.
        """
        self.log_file_path = log_file_path
        self._setup_logger()

    def _setup_logger(self):
        """
        Sets up a dedicated logger to write to the audit file.
        This ensures audit logs don't get mixed with application logs.
        """
        self.audit_logger = logging.getLogger('AuditLogger')
        self.audit_logger.setLevel(logging.INFO)

        # Prevent audit logs from propagating to the root logger
        self.audit_logger.propagate = False

        # Create a file handler for the audit log
        try:
            handler = logging.FileHandler(self.log_file_path)
            # No formatter is needed as we will write pre-formatted JSON
            self.audit_logger.addHandler(handler)
            logging.info(f"AuditLogger initialized. Logging to {self.log_file_path}")
        except Exception as e:
            logging.error(f"Failed to initialize AuditLogger file handler at {self.log_file_path}: {e}")
            raise

    def log(self, user: str, action: str, details: dict):
        """
        Logs an audit entry.

        Args:
            user (str): The user or system component responsible for the action.
            action (str): A string identifier for the action (e.g., 'RESOLVE_ALARM').
            details (dict): A dictionary with context-specific information about the event.
        """
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user": user,
                "action": action,
                "details": details
            }
            # Convert to JSON string and log it
            log_line = json.dumps(log_entry)
            self.audit_logger.info(log_line)
        except Exception as e:
            # Fallback to standard logging if audit logging fails
            logging.error(f"Failed to write to audit log: {e}")
            logging.error(f"Original audit message that failed: user={user}, action={action}")
