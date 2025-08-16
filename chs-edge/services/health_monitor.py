import psutil
import logging
from engine.executor import Executor, ExecutorState

class HealthMonitor:
    """
    Monitors the health of the edge device, including system resources and application state.
    """
    def __init__(self, executor: Executor):
        """
        Initializes the HealthMonitor.

        Args:
            executor: The application's main Executor instance.
        """
        self.executor = executor
        if not hasattr(psutil, 'sensors_battery'):
             psutil.sensors_battery = lambda: None # Mock battery on systems without it

    def get_health_status(self) -> dict:
        """
        Collects and returns a snapshot of the system's health.

        Returns:
            A dictionary containing key health metrics.
        """
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            # Application state
            # We access the state via the executor's public property
            app_state = self.executor.state.name

            health_data = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_info.percent,
                "disk_usage_percent": disk_info.percent,
                "app_state": app_state
            }
            return health_data

        except Exception as e:
            logging.error(f"Failed to get health status: {e}")
            return {
                "error": str(e)
            }
