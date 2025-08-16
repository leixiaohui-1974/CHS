import threading
from typing import Dict, Any

class StatusStore:
    """
    A thread-safe in-memory store for device statuses.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def update_device_status(self, device_id: str, data: Dict[str, Any]):
        """
        Updates the status for a given device.
        The data payload is expected to contain 'timestamp' and 'values'.
        """
        with self._lock:
            self._store[device_id] = {
                "timestamp": data.get("timestamp"),
                "values": data.get("values")
            }

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a copy of the entire status snapshot.
        """
        with self._lock:
            # Return a copy to prevent race conditions where the caller's
            # data could be modified by another thread.
            return self._store.copy()
