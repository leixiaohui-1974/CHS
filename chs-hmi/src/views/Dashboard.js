import React, { useState, useEffect } from 'react';
import { fetchSystemStatus, fetchEvents, fetchDeviceHistory } from '../services/apiService';
import websocketService from '../services/websocketService';
import DeviceCard from '../components/DeviceCard';
import EventList from '../components/EventList';
import Modal from '../components/Modal';
import HistoricalChart from '../components/HistoricalChart';

const Dashboard = () => {
  // Existing state
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState('');
  const [decisionRequests, setDecisionRequests] = useState({});

  // New state for Phase 3
  const [events, setEvents] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState({
    deviceId: null,
    sensorKey: null,
    historyData: null,
    isLoading: false,
    error: null,
  });

  // --- STYLES ---
  const headerStyle = {
    width: '100%',
    textAlign: 'center',
    marginBottom: '20px',
  };

  const dashboardContainerStyle = {
    display: 'flex',
    flexDirection: 'row',
    padding: '20px',
    gap: '20px',
    alignItems: 'flex-start',
  };

  const devicesContainerStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    flex: 3, // Takes up more space
  };

  const eventsContainerStyle = {
    flex: 1, // Takes up less space
    maxWidth: '450px',
  };

  const errorStyle = {
    color: 'red',
    width: '100%',
    textAlign: 'center',
  };

  // --- EFFECTS ---

  // Effect for polling system status (existing)
  useEffect(() => {
    const getData = async () => {
      try {
        const data = await fetchSystemStatus();
        setSystemStatus(data);
        setError('');
      } catch (err) {
        setError(err.message);
        console.error(err);
      }
    };
    getData();
    const intervalId = setInterval(getData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  // Effect for polling events (new)
  useEffect(() => {
    const getEvents = async () => {
      try {
        const eventData = await fetchEvents();
        const sortedEvents = eventData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setEvents(sortedEvents);
      } catch (err) {
        console.error("Failed to fetch events:", err.message);
      }
    };
    getEvents();
    const intervalId = setInterval(getEvents, 15000);
    return () => clearInterval(intervalId);
  }, []);

  // Effect for WebSocket connection (existing)
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

  // Effect to fetch history data when modal opens
  useEffect(() => {
    if (isModalOpen && modalContent.deviceId && modalContent.sensorKey) {
      const getHistory = async (range = '1h') => {
        setModalContent(prev => ({ ...prev, isLoading: true, error: null }));
        try {
          const history = await fetchDeviceHistory(modalContent.deviceId, range);
          const sensorHistory = history[modalContent.sensorKey];
          if (!sensorHistory || !sensorHistory.timestamps || !sensorHistory.values) {
            throw new Error(`No valid history data found for sensor '${modalContent.sensorKey}'`);
          }
          setModalContent(prev => ({ ...prev, historyData: sensorHistory, isLoading: false }));
        } catch (err) {
          console.error("Failed to fetch history:", err);
          setModalContent(prev => ({ ...prev, error: err.message, isLoading: false }));
        }
      };
      getHistory();
    }
  }, [isModalOpen, modalContent.deviceId, modalContent.sensorKey]);

  // --- HANDLERS ---

  const handleDecision = (deviceId, action) => {
    websocketService.sendDecision(deviceId, action);
    setDecisionRequests((prev) => {
      const newRequests = { ...prev };
      delete newRequests[deviceId];
      return newRequests;
    });
  };

  const handleSensorClick = (deviceId, sensorKey) => {
    setModalContent({
      deviceId,
      sensorKey,
      historyData: null,
      isLoading: true,
      error: null,
    });
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setModalContent({ deviceId: null, sensorKey: null, historyData: null, isLoading: false, error: null });
  };

  // --- RENDER ---
  return (
    <div>
      <div style={headerStyle}>
        <h1>CHS 综合监控仪表盘</h1>
      </div>
      {error && <p style={errorStyle}>Error: {error}</p>}

      <div style={dashboardContainerStyle}>
        <div style={devicesContainerStyle}>
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
                  onSensorClick={handleSensorClick}
                />
              );
            })
          ) : (
            !error && <p>Loading system status...</p>
          )}
        </div>

        <div style={eventsContainerStyle}>
          <EventList events={events} />
        </div>
      </div>

      <Modal
        show={isModalOpen}
        onClose={handleCloseModal}
        title={`历史数据: ${modalContent.sensorKey}`}
      >
        {modalContent.isLoading && <p>正在加载历史数据...</p>}
        {modalContent.error && <p style={errorStyle}>错误: {modalContent.error}</p>}
        {modalContent.historyData && (
          <HistoricalChart
            chartData={modalContent.historyData}
            title={`${modalContent.sensorKey} (最近1小时)`}
          />
        )}
      </Modal>
    </div>
  );
};

export default Dashboard;
