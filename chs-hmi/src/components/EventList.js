import React from 'react';

/**
 * A component to display a list of events or alarms with actions.
 * @param {object} props - The component's props.
 * @param {Array<object>} props.events - An array of event objects.
 * @param {function} props.onAcknowledge - Handler for acknowledging an event.
 * @param {function} props.onResolve - Handler for resolving an event.
 */
const EventList = ({ events, onAcknowledge, onResolve }) => {
  const containerStyle = {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '16px',
    margin: '16px',
    width: '400px',
    fontFamily: 'sans-serif',
    backgroundColor: '#f9f9f9',
  };

  const headerStyle = {
    margin: '0 0 12px 0',
    fontSize: '1.5em',
    color: '#333',
  };

  const listStyle = {
    listStyle: 'none',
    padding: '0',
    margin: '0',
    maxHeight: '500px',
    overflowY: 'auto',
  };

  const getEventItemStyle = (status) => {
    let backgroundColor = '#fff';
    if (status === 'ACKNOWLEDGED') {
      backgroundColor = '#f0f0f0'; // Grey out acknowledged events
    } else if (status === 'RESOLVED') {
      backgroundColor = '#e0ffe0'; // Light green for resolved events
    }
    return {
      display: 'flex',
      flexWrap: 'wrap',
      padding: '10px',
      borderBottom: '1px solid #eee',
      alignItems: 'center',
      backgroundColor,
    };
  };

  const getLevelStyle = (level) => {
    switch (level) {
      case 'WARNING':
        return { color: '#ffc107', fontWeight: 'bold' };
      case 'INFO':
        return { color: '#007bff', fontWeight: 'bold' };
      default:
        return { color: '#6c757d', fontWeight: 'bold' };
    }
  };

  const infoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
  };

  const timestampStyle = {
    fontSize: '0.85em',
    color: '#666',
    marginRight: '12px',
    minWidth: '150px',
  };

  const messageStyle = {
    flex: 1,
  };

  const actionsContainerStyle = {
    width: '100%',
    textAlign: 'right',
    marginTop: '8px',
  };

  const buttonStyle = {
    marginLeft: '8px',
    padding: '4px 8px',
    fontSize: '0.8em',
    cursor: 'pointer',
    border: '1px solid #ccc',
    borderRadius: '4px',
  };

  if (!events || events.length === 0) {
    return (
      <div style={containerStyle}>
        <h3 style={headerStyle}>事件与告警</h3>
        <p>当前没有事件。</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h3 style={headerStyle}>事件与告警</h3>
      <ul style={listStyle}>
        {events.map((event) => (
          <li key={event.id} style={getEventItemStyle(event.status)}>
            <div style={infoContainerStyle}>
              <span style={timestampStyle}>
                {new Date(event.timestamp).toLocaleString()}
              </span>
              <span style={{ ...getLevelStyle(event.level), marginRight: '12px' }}>
                [{event.level}]
              </span>
              <span style={messageStyle}>{event.message}</span>
            </div>
            <div style={actionsContainerStyle}>
              {event.status === 'ACTIVE' && (
                <>
                  <button style={buttonStyle} onClick={() => onAcknowledge(event.id)}>
                    确认
                  </button>
                  <button style={buttonStyle} onClick={() => onResolve(event.id)}>
                    解决
                  </button>
                </>
              )}
              {event.status === 'ACKNOWLEDGED' && (
                <button style={buttonStyle} onClick={() => onResolve(event.id)}>
                  解决
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EventList;
