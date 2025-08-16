import React, { useState, useEffect } from 'react';
import { fetchSystemStatus, fetchEvents, fetchDeviceHistory, acknowledgeEvent, resolveEvent } from '../services/apiService';
import websocketService from '../services/websocketService';
import DeviceCard from '../components/DeviceCard';
import EventList from '../components/EventList';
import Modal from '../components/Modal';
import HistoricalChart from '../components/HistoricalChart';
import NavTabs from '../components/NavTabs';
import TopologyView from '../components/TopologyView';
import DeviceSettings from '../components/DeviceSettings';

const Dashboard = () => {
  // --- STATE ---
  const [systemStatus, setSystemStatus] = useState(null);
  const [error, setError] = useState('');
  const [decisionRequests, setDecisionRequests] = useState({});
  const [events, setEvents] = useState([]);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [historyModalContent, setHistoryModalContent] = useState({
    deviceId: null,
    sensorKey: null,
    historyData: null,
    isLoading: false,
    error: null,
  });
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolvingEvent, setResolvingEvent] = useState({ id: null, notes: '' });
  const [activeView, setActiveView] = useState('dashboard'); // 'dashboard', 'topology', 'settings'

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
    flex: 3,
  };

  const eventsContainerStyle = {
    flex: 1,
    maxWidth: '450px',
  };

  const errorStyle = {
    color: 'red',
    width: '100%',
    textAlign: 'center',
  };

  // --- EFFECTS ---
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

  useEffect(() => {
    if (isHistoryModalOpen && historyModalContent.deviceId && historyModalContent.sensorKey) {
      const getHistory = async (range = '1h') => {
        setHistoryModalContent(prev => ({ ...prev, isLoading: true, error: null }));
        try {
          const history = await fetchDeviceHistory(historyModalContent.deviceId, range);
          const sensorHistory = history[historyModalContent.sensorKey];
          if (!sensorHistory || !sensorHistory.timestamps || !sensorHistory.values) {
            throw new Error(`No valid history data found for sensor '${historyModalContent.sensorKey}'`);
          }
          setHistoryModalContent(prev => ({ ...prev, historyData: sensorHistory, isLoading: false }));
        } catch (err) {
          console.error("Failed to fetch history:", err);
          setHistoryModalContent(prev => ({ ...prev, error: err.message, isLoading: false }));
        }
      };
      getHistory();
    }
  }, [isHistoryModalOpen, historyModalContent.deviceId, historyModalContent.sensorKey]);

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
    setHistoryModalContent({
      deviceId,
      sensorKey,
      historyData: null,
      isLoading: true,
      error: null,
    });
    setIsHistoryModalOpen(true);
  };

  const handleCloseHistoryModal = () => {
    setIsHistoryModalOpen(false);
    setHistoryModalContent({ deviceId: null, sensorKey: null, historyData: null, isLoading: false, error: null });
  };

  const handleAcknowledgeEvent = async (eventId) => {
    try {
      await acknowledgeEvent(eventId);
      setEvents(prevEvents =>
        prevEvents.map(event =>
          event.id === eventId ? { ...event, status: 'ACKNOWLEDGED' } : event
        )
      );
    } catch (err) {
      setError(`Failed to acknowledge event: ${err.message}`);
    }
  };

  const handleOpenResolveModal = (eventId) => {
    setResolvingEvent({ id: eventId, notes: '' });
    setIsResolveModalOpen(true);
  };

  const handleCloseResolveModal = () => {
    setIsResolveModalOpen(false);
    setResolvingEvent({ id: null, notes: '' });
  };

  const handleResolveEvent = async () => {
    if (!resolvingEvent.id) return;
    try {
      await resolveEvent(resolvingEvent.id, resolvingEvent.notes);
      setEvents(prevEvents =>
        prevEvents.map(event =>
          event.id === resolvingEvent.id ? { ...event, status: 'RESOLVED' } : event
        )
      );
      handleCloseResolveModal();
    } catch (err) {
      setError(`Failed to resolve event: ${err.message}`);
    }
  };

  // --- RENDER ---
  const renderActiveView = () => {
    switch (activeView) {
      case 'topology':
        return <TopologyView />;
      case 'settings':
        return <DeviceSettings />;
      case 'dashboard':
      default:
        return (
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
              <EventList
                events={events}
                onAcknowledge={handleAcknowledgeEvent}
                onResolve={handleOpenResolveModal}
              />
            </div>
          </div>
        );
    }
  };

  return (
    <div>
      <div style={headerStyle}>
        <h1>CHS 运管一体化平台</h1>
      </div>
      <NavTabs activeView={activeView} onSelectView={setActiveView} />
      {error && <p style={errorStyle}>Error: {error}</p>}

      {renderActiveView()}

      <Modal
        show={isHistoryModalOpen}
        onClose={handleCloseHistoryModal}
        title={`历史数据: ${historyModalContent.sensorKey}`}
      >
        {historyModalContent.isLoading && <p>正在加载历史数据...</p>}
        {historyModalContent.error && <p style={errorStyle}>错误: {historyModalContent.error}</p>}
        {historyModalContent.historyData && (
          <HistoricalChart
            chartData={historyModalContent.historyData}
            title={`${historyModalContent.sensorKey} (最近1小时)`}
          />
        )}
      </Modal>

      <Modal
        show={isResolveModalOpen}
        onClose={handleCloseResolveModal}
        title={`解决告警: ${resolvingEvent.id}`}
      >
        <div>
          <label htmlFor="resolveNotes" style={{ display: 'block', marginBottom: '8px' }}>
            解决备注:
          </label>
          <textarea
            id="resolveNotes"
            style={{ width: '100%', minHeight: '80px', padding: '8px' }}
            value={resolvingEvent.notes}
            onChange={(e) => setResolvingEvent(prev => ({ ...prev, notes: e.target.value }))}
          />
          <button
            style={{ marginTop: '10px', padding: '8px 16px' }}
            onClick={handleResolveEvent}
          >
            提交
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;
