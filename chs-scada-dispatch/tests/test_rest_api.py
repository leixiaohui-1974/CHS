import pytest
import json
from unittest.mock import MagicMock
from api.rest_api import create_rest_app

# --- Mock Services ---
@pytest.fixture
def mock_timeseries_db():
    return MagicMock()

@pytest.fixture
def mock_event_store():
    return MagicMock()

@pytest.fixture
def mock_mqtt_service():
    return MagicMock()

@pytest.fixture
def mock_audit_logger():
    return MagicMock()

@pytest.fixture
def app(mock_timeseries_db, mock_event_store, mock_mqtt_service, mock_audit_logger):
    """Create a Flask app instance for testing."""
    app = create_rest_app(
        timeseries_db=mock_timeseries_db,
        event_store=mock_event_store,
        mqtt_service=mock_mqtt_service,
        audit_logger=mock_audit_logger
    )
    app.config.update({"TESTING": True})
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# --- API Tests ---

def test_acknowledge_event_api(client, mock_event_store, mock_audit_logger):
    """Test the POST /api/v1/events/{event_id}/ack endpoint."""
    event_id = "evt-123"
    request_body = {"user": "api_tester"}

    # Configure mock to return success
    mock_event_store.acknowledge_event.return_value = True

    response = client.post(f'/api/v1/events/{event_id}/ack', json=request_body)

    assert response.status_code == 200
    assert response.json['message'] == f"Event {event_id} acknowledged."

    # Verify that the underlying service and logger were called correctly
    mock_event_store.acknowledge_event.assert_called_once_with(event_id, "api_tester")
    mock_audit_logger.log.assert_called_once_with("api_tester", 'ACKNOWLEDGE_EVENT', {'event_id': event_id})

def test_resolve_event_api(client, mock_event_store, mock_audit_logger):
    """Test the POST /api/v1/events/{event_id}/resolve endpoint."""
    event_id = "evt-456"
    request_body = {"user": "api_resolver", "notes": "Resolved via API test."}

    mock_event_store.resolve_event.return_value = True

    response = client.post(f'/api/v1/events/{event_id}/resolve', json=request_body)

    assert response.status_code == 200
    assert response.json['message'] == f"Event {event_id} resolved."

    mock_event_store.resolve_event.assert_called_once_with(event_id, "api_resolver", "Resolved via API test.")
    mock_audit_logger.log.assert_called_once_with("api_resolver", 'RESOLVE_EVENT', {'event_id': event_id, 'notes': "Resolved via API test."})

def test_update_device_config_api(client, mock_mqtt_service, mock_audit_logger):
    """Test the POST /api/v1/devices/{device_id}/config endpoint."""
    device_id = "edge-device-007"
    request_body = {
        "user": "config_updater",
        "version": "2.1.0",
        "parameters": {"high_level": 155.0}
    }

    response = client.post(f'/api/v1/devices/{device_id}/config', json=request_body)

    assert response.status_code == 202
    assert response.json['message'] == f"Configuration update sent to device {device_id}."

    # The 'user' field is for auditing and should be removed before publishing
    expected_config_payload = {
        "version": "2.1.0",
        "parameters": {"high_level": 155.0}
    }

    mock_mqtt_service.publish_config.assert_called_once_with(device_id, expected_config_payload)
    mock_audit_logger.log.assert_called_once_with("config_updater", 'UPDATE_DEVICE_CONFIG', {'device_id': device_id, 'config': expected_config_payload})

def test_post_command_with_audit(client, mock_mqtt_service, mock_audit_logger):
    """Test the existing POST /api/v1/command endpoint to ensure auditing was added."""
    device_id = "device-abc"
    request_body = {"user": "commander", "target_device_id": device_id, "command": {"action": "START"}}

    response = client.post('/api/v1/command', json=request_body)

    assert response.status_code == 202

    mock_mqtt_service.publish_command.assert_called_once_with(device_id, {"action": "START"})
    mock_audit_logger.log.assert_called_once_with("commander", 'SEND_COMMAND', {'device_id': device_id, 'command': {"action": "START"}})
