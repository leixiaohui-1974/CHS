import React, { useState, useEffect } from 'react';
import { fetchSystemStatus } from '../services/apiService';
import websocketService from '../services/websocketService';
import DeviceCard from '../components/DeviceCard';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState('');
  const [decisionRequests, setDecisionRequests] = useState({});

  const containerStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    padding: '20px',
  };

  const headerStyle = {
    width: '100%',
    textAlign: 'center',
    marginBottom: '20px',
  };

  const errorStyle = {
    color: 'red',
    width: '100%',
    textAlign: 'center',
  };

  // Effect for polling system status
  useEffect(() => {
    const getData = async () => {
      try {
        const data = await fetchSystemStatus();
        setSystemStatus(data);
        setError(''); // Clear any previous errors
      } catch (err) {
        setError(err.message);
        console.error(err); // Also log the full error to the console
      }
    };

    getData();
    const intervalId = setInterval(getData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  // Effect for WebSocket connection
  useEffect(() => {
    const handleDecisionRequest = (request) => {
      setDecisionRequests((prev) => ({
        ...prev,
        [request.device_id]: {
          message: request.message,
          options: request.options,
        },
      }));
    };

    websocketService.connect(handleDecisionRequest);

    return () => {
      websocketService.disconnect();
    };
  }, []);

  const handleDecision = (deviceId, action) => {
    // Send decision to backend
    websocketService.sendDecision(deviceId, action);

    // Immediately hide the decision UI
    setDecisionRequests((prev) => {
      const newRequests = { ...prev };
      delete newRequests[deviceId];
      return newRequests;
    });
  };

  return (
    <div>
      <div style={headerStyle}>
        <h1>CHS 系统实时状态看板</h1>
      </div>
      {error && <p style={errorStyle}>Error: {error}</p>}
      <div style={containerStyle}>
        {systemStatus ? (
          Object.entries(systemStatus).map(([deviceId, deviceData]) => {
            const decisionInfo = decisionRequests[deviceId];
            return (
              <DeviceCard
                key={deviceId}
                deviceId={deviceId}
                deviceData={deviceData}
                isAwaitingDecision={!!decisionInfo}
                decisionInfo={decisionInfo}
                onDecision={handleDecision}
              />
            );
          })
        ) : (
          !error && <p>Loading system status...</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
