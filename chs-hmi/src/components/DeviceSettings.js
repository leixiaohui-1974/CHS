import React, { useState } from 'react';
import { mockDeviceConfigs } from '../mockData';
import { updateDeviceConfig } from '../services/apiService';

const DeviceSettings = () => {
  const [selectedDevice, setSelectedDevice] = useState('');
  const [config, setConfig] = useState(null);
  const [feedback, setFeedback] = useState({ message: '', type: '' });

  const handleDeviceChange = (e) => {
    const deviceId = e.target.value;
    setSelectedDevice(deviceId);
    if (deviceId && mockDeviceConfigs[deviceId]) {
      setConfig(mockDeviceConfigs[deviceId].config);
    } else {
      setConfig(null);
    }
    setFeedback({ message: '', type: '' });
  };

  const handleConfigChange = (e) => {
    const { name, value } = e.target;
    const isNumber = !isNaN(parseFloat(value)) && isFinite(value);
    setConfig(prevConfig => ({
      ...prevConfig,
      [name]: isNumber ? parseFloat(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedDevice || !config) return;

    try {
      await updateDeviceConfig(selectedDevice, config);
      setFeedback({ message: `设备 ${selectedDevice} 的配置已成功更新。`, type: 'success' });
    } catch (err) {
      setFeedback({ message: `更新失败: ${err.message}`, type: 'error' });
    }
  };

  const containerStyle = {
    padding: '20px',
    maxWidth: '600px',
    margin: '0 auto',
    fontFamily: 'sans-serif',
  };

  const formGroupStyle = {
    marginBottom: '15px',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '5px',
    fontWeight: 'bold',
  };

  const inputStyle = {
    width: '100%',
    padding: '8px',
    boxSizing: 'border-box',
    borderRadius: '4px',
    border: '1px solid #ccc',
  };

  const buttonStyle = {
      padding: '10px 15px',
      border: 'none',
      backgroundColor: '#007bff',
      color: 'white',
      borderRadius: '4px',
      cursor: 'pointer'
  };

  return (
    <div style={containerStyle}>
      <h2 style={{ textAlign: 'center' }}>远程配置管理</h2>
      <div style={formGroupStyle}>
        <label htmlFor="device-select" style={labelStyle}>选择设备:</label>
        <select id="device-select" value={selectedDevice} onChange={handleDeviceChange} style={inputStyle}>
          <option value="">-- 请选择一个设备 --</option>
          {Object.keys(mockDeviceConfigs).map(deviceId => (
            <option key={deviceId} value={deviceId}>
              {mockDeviceConfigs[deviceId].name} ({deviceId})
            </option>
          ))}
        </select>
      </div>

      {config && (
        <form onSubmit={handleSubmit}>
          {Object.entries(config).map(([key, value]) => (
            <div key={key} style={formGroupStyle}>
              <label htmlFor={key} style={labelStyle}>{key}:</label>
              <input
                type={typeof value === 'number' ? 'number' : 'text'}
                id={key}
                name={key}
                value={value}
                onChange={handleConfigChange}
                style={inputStyle}
                step={typeof value === 'number' ? '0.1' : undefined}
              />
            </div>
          ))}
          <button type="submit" style={buttonStyle}>保存配置</button>
        </form>
      )}

      {feedback.message && (
        <p style={{
          color: feedback.type === 'error' ? 'red' : 'green',
          marginTop: '15px'
        }}>
          {feedback.message}
        </p>
      )}
    </div>
  );
};

export default DeviceSettings;
