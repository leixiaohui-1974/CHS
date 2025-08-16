import React from 'react';

/**
 * A card component to display the status of a single device, with added HITL capabilities.
 * @param {object} props - The component's props.
 * @param {string} props.deviceId - The ID of the device.
 * @param {object} props.deviceData - The data object for the device.
 * @param {boolean} props.isAwaitingDecision - Whether a decision is awaited for this device.
 * @param {object} props.decisionInfo - Information related to the decision.
 * @param {string} props.decisionInfo.message - The message prompt for the user.
 * @param {Array<object>} props.decisionInfo.options - The available decision options.
 * @param {function} props.onDecision - Callback function to handle the user's decision.
 */
const DeviceCard = ({ deviceId, deviceData, isAwaitingDecision, decisionInfo, onDecision }) => {
  const cardStyle = {
    border: '1px solid #ccc',
    borderRadius: '8px',
    padding: '16px',
    margin: '16px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    width: '300px',
    fontFamily: 'sans-serif',
    // Highlight the card if a decision is needed
    backgroundColor: isAwaitingDecision ? '#fffadd' : '#fff',
    transition: 'background-color 0.3s ease',
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

  const decisionContainerStyle = {
    marginTop: '16px',
    padding: '12px',
    border: '1px solid #ffc107',
    borderRadius: '4px',
    backgroundColor: '#fff9e6',
  };

  const decisionMessageStyle = {
    fontWeight: 'bold',
    marginBottom: '12px',
  };

  const buttonContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  };

  const buttonStyle = {
    padding: '10px 15px',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#007bff',
    color: 'white',
    cursor: 'pointer',
    textAlign: 'center',
    fontSize: '1em',
  };

  const handleDecision = (action) => {
    if (onDecision) {
      onDecision(deviceId, action);
    }
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

      {isAwaitingDecision && decisionInfo && (
        <div style={decisionContainerStyle}>
          <p style={decisionMessageStyle}>{decisionInfo.message}</p>
          <div style={buttonContainerStyle}>
            {decisionInfo.options.map((option, index) => (
              <button
                key={index}
                style={buttonStyle}
                onClick={() => handleDecision(option.action)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceCard;
