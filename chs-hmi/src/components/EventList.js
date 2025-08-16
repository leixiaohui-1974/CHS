import React from 'react';

/**
 * A component to display a list of events or alarms.
 * @param {object} props - The component's props.
 * @param {Array<object>} props.events - An array of event objects.
 *        Each object should have `timestamp`, `level`, and `message`.
 */
const EventList = ({ events }) => {
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

  const eventItemStyle = {
    display: 'flex',
    padding: '10px',
    borderBottom: '1px solid #eee',
    alignItems: 'center',
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

  const timestampStyle = {
    fontSize: '0.85em',
    color: '#666',
    marginRight: '12px',
    minWidth: '150px',
  };

  const messageStyle = {
    flex: 1,
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
        {events.map((event, index) => (
          <li key={index} style={eventItemStyle}>
            <span style={timestampStyle}>
              {new Date(event.timestamp).toLocaleString()}
            </span>
            <span style={{...getLevelStyle(event.level), marginRight: '12px'}}>
              [{event.level}]
            </span>
            <span style={messageStyle}>{event.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EventList;
