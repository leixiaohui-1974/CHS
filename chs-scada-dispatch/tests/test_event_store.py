import pytest
from unittest.mock import MagicMock, patch
from data_processing.event_store import EventStore
import os

# Set dummy env vars for testing
os.environ["INFLUXDB_URL"] = "http://localhost:8086"
os.environ["INFLUXDB_TOKEN"] = "test-token"
os.environ["INFLUXDB_ORG"] = "test-org"
os.environ["INFLUXDB_EVENTS_BUCKET"] = "test-bucket"

@pytest.fixture
def mock_influx_client():
    """Fixture to mock the InfluxDB client and its APIs."""
    with patch('data_processing.event_store.InfluxDBClient') as mock_client_constructor:
        mock_client_instance = MagicMock()
        mock_client_instance.write_api.return_value = MagicMock()
        mock_client_instance.query_api.return_value = MagicMock()
        mock_client_instance.delete_api.return_value = MagicMock()
        mock_client_constructor.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def event_store(mock_influx_client):
    """Fixture to create an EventStore instance with a mocked client."""
    store = EventStore()
    # Replace client instance with our mock
    store.client = mock_influx_client
    store.write_api = mock_influx_client.write_api()
    store.query_api = mock_influx_client.query_api()
    store.delete_api = mock_influx_client.delete_api()
    return store

def test_add_event_generates_id(event_store, mock_influx_client):
    """Test that add_event generates a UUID if no event_id is provided."""
    event_data = {"type": "ALARM", "source": "device1", "severity": "CRITICAL", "message": "Test Alarm"}
    event_store.add_event(event_data)

    # Check that write was called
    event_store.write_api.write.assert_called_once()
    # Get the 'record' argument from the call
    args, kwargs = event_store.write_api.write.call_args
    written_point = kwargs['record']

    # Verify the point has an event_id tag
    assert 'event_id' in written_point._tags
    assert len(written_point._tags['event_id']) == 36 # Length of a UUID string

def test_acknowledge_event(event_store, mock_influx_client):
    """Test the full acknowledge workflow: get, delete, write."""
    event_id = "test-event-123"
    user = "test-user"

    # 1. Mock the return value of get_event
    mock_event_data = {
        'event_id': event_id,
        'type': 'ALARM',
        'status': 'NEW',
        '_time': '2023-01-01T00:00:00Z'
    }
    # We need to mock the query result to simulate get_event finding an event
    mock_query_api = event_store.query_api
    mock_table = MagicMock()
    mock_record = MagicMock()
    mock_record.values = mock_event_data
    mock_table.records = [mock_record]
    mock_query_api.query.return_value = [mock_table]

    # 2. Call the method to test
    result = event_store.acknowledge_event(event_id, user)

    # 3. Assertions
    assert result is True
    # Check that get_event query was made
    mock_query_api.query.assert_called()
    # Check that delete was called correctly
    event_store.delete_api.delete.assert_called_once()
    delete_args, delete_kwargs = event_store.delete_api.delete.call_args
    assert f'event_id="{event_id}"' in delete_args[2] # predicate is the 3rd positional arg
    # Check that write was called to re-insert the event with updated status
    event_store.write_api.write.assert_called_once()
    write_args, write_kwargs = event_store.write_api.write.call_args
    updated_point = write_kwargs['record']
    assert updated_point._tags['status'] == 'ACKNOWLEDGED'
    assert updated_point._fields['acknowledged_by'] == user

def test_resolve_event(event_store, mock_influx_client):
    """Test the full resolve workflow: get, delete, write."""
    event_id = "test-event-456"
    user = "resolver-user"
    notes = "Device restarted."

    # Mock get_event
    mock_event_data = {'event_id': event_id, 'type': 'ALARM', 'status': 'ACKNOWLEDGED', '_time': '2023-01-01T00:00:00Z'}
    mock_query_api = event_store.query_api
    mock_table = MagicMock()
    mock_record = MagicMock()
    mock_record.values = mock_event_data
    mock_table.records = [mock_record]
    mock_query_api.query.return_value = [mock_table]

    # Call the method
    result = event_store.resolve_event(event_id, user, notes)

    # Assertions
    assert result is True
    event_store.delete_api.delete.assert_called_once()
    event_store.write_api.write.assert_called_once()
    updated_point = event_store.write_api.write.call_args.kwargs['record']
    assert updated_point._tags['status'] == 'RESOLVED'
    assert updated_point._fields['resolved_by'] == user
    assert updated_point._fields['resolution_notes'] == notes
