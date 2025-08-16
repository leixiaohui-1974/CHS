import React from 'react';

/**
 * A card component to display the status of a single device.
 * @param {object} props - The component's props.
 * @param {string} props.deviceId - The ID of the device.
 * @param {object} props.deviceData - The data object for the device.
 * @param {string} props.deviceData.timestamp - The timestamp of the data.
 * @param {object} props.deviceData.values - A map of sensor keys to their values.
 */
const DeviceCard = ({ deviceId, deviceData }) => {
  const cardStyle = {
    border: '1px solid #ccc',
    borderRadius: '8px',
    padding: '16px',
    margin: '16px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    width: '300px',
    fontFamily: 'sans-serif',
  };

  const headerStyle = {
    borderBottom: '1px solid #eee',
    paddingBottom: '8px',
    marginBottom: '12px',
  };

  const titleStyle = {
    margin: '0',
    fontSize: '1.25em',
  };

  const timestampStyle = {
    fontSize: '0.8em',
    color: '#666',
    marginTop: '4px',
  };

  const valuesListStyle = {
    listStyle: 'none',
    padding: '0',
    margin: '0',
  };

  const valueItemStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '4px 0',
  };

  // It's possible that deviceData or its properties are not yet available
  if (!deviceData) {
    return (
      <div style={cardStyle}>
        <div style={headerStyle}>
          <h3 style={titleStyle}>{deviceId}</h3>
        </div>
        <p>No data available.</p>
      </div>
    );
  }

  const { timestamp, values } = deviceData;

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>
        <h3 style={titleStyle}>{deviceId}</h3>
        {timestamp && (
          <p style={timestampStyle}>
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        )}
      </div>
      <ul style={valuesListStyle}>
        {values && Object.entries(values).map(([key, value]) => (
          <li key={key} style={valueItemStyle}>
            <span>{key.replace(/_/g, ' ')}:</span>
            <strong>{typeof value === 'number' ? value.toFixed(2) : value}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DeviceCard;
