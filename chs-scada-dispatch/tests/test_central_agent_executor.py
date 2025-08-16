import unittest
import time
import threading
from unittest.mock import Mock, MagicMock, call

from dispatch_engine.central_agent_executor import CentralExecutor

class TestCentralAgentExecutorHITL(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test."""
        self.mock_timeseries_db = Mock()
        self.mock_mqtt_service = Mock()
        self.mock_socketio = MagicMock()

        self.executor = CentralExecutor(
            timeseries_db=self.mock_timeseries_db,
            mqtt_service=self.mock_mqtt_service,
            websocket_service=self.mock_socketio
        )
        # Lower the interval for faster testing
        self.executor.decision_interval_sec = 0.1
        self.executor.load_agent("dummy/path")

    def test_hitl_approve_and_reject_flow(self):
        """Test both HITL approve and reject flows."""
        # --- Test Data ---
        hitl_observation = {
            "pump_station_01": {
                "values": {"pressure_psi": 115},
                "timestamp": "2023-10-27T10:00:00Z"
            }
        }
        no_action_observation = {"pump_station_01": {"values": {"pressure_psi": 100}}}

        # --- Mock setup ---
        # The first time it's called, it returns data that triggers HITL.
        # The second time, it returns normal data to allow the loop to continue.
        self.mock_timeseries_db.get_latest_statuses.side_effect = [
            hitl_observation,
            no_action_observation,
            hitl_observation,
            no_action_observation
        ]

        # --- Events for synchronization ---
        request_emitted_event = threading.Event()

        # We need to capture the arguments passed to emit
        hitl_request_args = {}
        def capture_emit(*args, **kwargs):
            if args[0] == 'decision_request':
                hitl_request_args['event_name'] = args[0]
                hitl_request_args['data'] = args[1]
                request_emitted_event.set()

        self.mock_socketio.emit.side_effect = capture_emit

        # --- Start executor in background thread ---
        self.executor.start()

        # --- TEST 1: APPROVE ---
        # Wait for the decision_request to be emitted
        was_emitted = request_emitted_event.wait(timeout=2)
        self.assertTrue(was_emitted, "HITL request was not emitted")

        # Get request_id and submit approval
        request_id = hitl_request_args['data']['request_id']
        self.executor.submit_human_decision(request_id, {"approved": True})

        # Give executor time to process the approval and publish
        time.sleep(0.2)

        # Assert MQTT publish was called correctly
        self.mock_mqtt_service.publish_command.assert_called_once_with(
            'pump_station_01', {'set_pump_speed': 0.9}
        )

        # --- Reset for next test ---
        self.mock_mqtt_service.reset_mock()
        request_emitted_event.clear()
        hitl_request_args.clear()

        # --- TEST 2: REJECT ---
        # Wait for the next decision_request
        was_emitted = request_emitted_event.wait(timeout=2)
        self.assertTrue(was_emitted, "Second HITL request was not emitted")

        # Get request_id and submit rejection
        request_id = hitl_request_args['data']['request_id']
        self.executor.submit_human_decision(request_id, {"approved": False})

        # Give executor time to process
        time.sleep(0.2)

        # Assert MQTT publish was NOT called
        self.mock_mqtt_service.publish_command.assert_not_called()

    def tearDown(self):
        """Clean up after each test."""
        self.executor.stop()

if __name__ == '__main__':
    unittest.main()
