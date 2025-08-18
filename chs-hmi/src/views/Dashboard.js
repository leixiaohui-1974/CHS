import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchSystemStatus,
  fetchEvents,
  fetchDeviceHistory,
  acknowledgeEvent,
  resolveEvent,
  fetchDashboardLayouts,
  saveDashboardLayout,
} from '../services/apiService';
import { Responsive, WidthProvider } from 'react-grid-layout';
import websocketService from '../services/websocketService';
import DeviceCard from '../components/DeviceCard';
import EventList from '../components/EventList';
import Modal from '../components/Modal';
import HistoricalChart from '../components/HistoricalChart';
import ReactFlowTopology from '../components/ReactFlowTopology';
import DeviceSettings from '../components/DeviceSettings';

const ResponsiveGridLayout = WidthProvider(Responsive);

const Dashboard = forwardRef(({ isEditMode, activeView, setActiveView }, ref) => {
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
  const [layouts, setLayouts] = useState(null);
  const { user } = useAuth();

  const defaultLayouts = {
    lg: [
      { i: 'devices', x: 0, y: 0, w: 8, h: 12, minW: 4, minH: 6 },
      { i: 'events', x: 8, y: 0, w: 4, h: 12, minW: 3, minH: 8 },
    ],
  };

  // Expose the saveLayout function to the parent component (Layout)
  useImperativeHandle(ref, () => ({
    saveLayout: async () => {
      try {
        await saveDashboardLayout(layouts);
        alert('Layout saved successfully!');
      } catch (error) {
        console.error("Failed to save layout:", error);
        alert(`Error saving layout: ${error.message}`);
      }
    },
  }));

  // --- STYLES ---
  const devicesContainerStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    width: '100%',
    height: '100%',
    overflow: 'auto',
  };

  const eventsContainerStyle = {
    width: '100%',
    height: '100%',
    overflow: 'auto',
  };

  const gridItemStyle = {
    border: isEditMode ? '1px dashed #ccc' : 'none',
    borderRadius: '4px',
    padding: '5px',
    backgroundColor: '#fff',
  };

    useEffect(() => {
        fetchProjectsAndModels();
    }, [fetchProjectsAndModels]);

    const handleOpenTrainModal = (project) => {
        setSelectedProject(project);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedProject(null);
    };

    const handleTrainingComplete = () => {
        // Refresh the data after training is done
        fetchProjectsAndModels();
    };

    const handleRun = async (projectId) => {
        try {
            alert(`Running simulation for project ${projectId}...`);
            await axios.post(`/api/projects/${projectId}/run`);
            alert(`Simulation for project ${projectId} completed!`);
        } catch (err) {
            alert(`Failed to run simulation for project ${projectId}.`);
            console.error(err);
        }
      };
      getHistory();
    }
  }, [isHistoryModalOpen, historyModalContent.deviceId, historyModalContent.sensorKey]);

  useEffect(() => {
    const loadLayout = async () => {
      const savedData = await fetchDashboardLayouts();
      if (savedData && savedData.layouts) {
        setLayouts(savedData.layouts);
      } else {
        setLayouts(defaultLayouts);
      }
    };
    loadLayout();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    setHistoryModalContent({ deviceId, sensorKey, historyData: null, isLoading: true, error: null });
    setIsHistoryModalOpen(true);
  };

  const handleCloseHistoryModal = () => {
    setIsHistoryModalOpen(false);
    setHistoryModalContent({ deviceId: null, sensorKey: null, historyData: null, isLoading: false, error: null });
  };

  const handleAcknowledgeEvent = async (eventId) => {
    try {
      await acknowledgeEvent(eventId);
      setEvents(prevEvents => prevEvents.map(event => event.id === eventId ? { ...event, status: 'ACKNOWLEDGED' } : event));
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
      setEvents(prevEvents => prevEvents.map(event => event.id === resolvingEvent.id ? { ...event, status: 'RESOLVED' } : event));
      handleCloseResolveModal();
    } catch (err) {
      setError(`Failed to resolve event: ${err.message}`);
    }
  };

  // --- RENDER ---
  const renderActiveView = () => {
    switch (activeView) {
      case 'topology':
        return <ReactFlowTopology />;
      case 'settings':
        return user?.role === 'admin' ? <DeviceSettings /> : <p>Access Denied</p>;
      case 'dashboard':
      default:
        return (
          <ResponsiveGridLayout
            className="layout"
            layouts={layouts || defaultLayouts}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 2 }}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={30}
            isDraggable={isEditMode}
            isResizable={isEditMode}
            onLayoutChange={(layout, newLayouts) => setLayouts(newLayouts)}
          >
            <div key="devices" style={gridItemStyle}>
              <div style={devicesContainerStyle}>
                {systemStatus ? (
                  Object.entries(systemStatus).map(([deviceId, deviceData]) => (
                    <DeviceCard
                      key={deviceId}
                      deviceId={deviceId}
                      deviceData={deviceData}
                      isAwaitingDecision={!!decisionRequests[deviceId]}
                      decisionInfo={decisionRequests[deviceId]}
                      onDecision={handleDecision}
                      onSensorClick={handleSensorClick}
                    />
                  ))
                ) : (
                  !error && <p>Loading system status...</p>
                )}
              </div>
            </div>
            <div key="events" style={gridItemStyle}>
              <div style={eventsContainerStyle}>
                <EventList
                  events={events}
                  onAcknowledge={handleAcknowledgeEvent}
                  onResolve={handleOpenResolveModal}
                />
              </div>
            </div>
          </ResponsiveGridLayout>
        );
    }
  };

  return (
    <div>
      {error && <p style={errorStyle}>{error}</p>}
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

            {isModalOpen && selectedProject && (
                <TrainingModal
                    project={selectedProject}
                    onClose={handleCloseModal}
                    onTrainingStarted={handleTrainingComplete}
                />
            )}
        </div>
      </Modal>
    </div>
  );
});

export default Dashboard;
