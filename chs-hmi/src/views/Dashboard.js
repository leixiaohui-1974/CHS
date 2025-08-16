import React, { useState, useEffect } from 'react';
import { fetchSystemStatus } from '../services/apiService';
import DeviceCard from '../components/DeviceCard';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState('');

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

    // Fetch data immediately on component mount
    getData();

    // Then set up an interval to fetch data every 5 seconds
    const intervalId = setInterval(getData, 5000);

    // Clean up the interval when the component unmounts
    return () => clearInterval(intervalId);
  }, []); // The empty dependency array ensures this effect runs only once on mount

  return (
    <div>
      <div style={headerStyle}>
        <h1>CHS 系统实时状态看板</h1>
      </div>
      {error && <p style={errorStyle}>Error: {error}</p>}
      <div style={containerStyle}>
        {systemStatus ? (
          Object.entries(systemStatus).map(([deviceId, deviceData]) => (
            <DeviceCard key={deviceId} deviceId={deviceId} deviceData={deviceData} />
          ))
        ) : (
          !error && <p>Loading system status...</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
