export const mockEvents = [
  { id: 'evt-1', timestamp: '2025-08-16T10:00:00Z', level: 'WARNING', message: 'Upstream reservoir level is high: 155.2m', status: 'ACTIVE' },
  { id: 'evt-2', timestamp: '2025-08-16T10:05:00Z', level: 'INFO', message: 'Pump station 1 activated.', status: 'RESOLVED' },
  { id: 'evt-3', timestamp: '2025-08-16T10:15:00Z', level: 'WARNING', message: 'Pump station 2 pressure anomaly: 3.5 bar', status: 'ACTIVE' },
  { id: 'evt-4', timestamp: '2025-08-16T10:16:00Z', level: 'WARNING', message: 'Pump station 2 pressure anomaly: 3.6 bar', status: 'ACKNOWLEDGED' },
  { id: 'evt-5', timestamp: '2025-08-16T10:20:00Z', level: 'INFO', message: 'Downstream sluice gate opened.', status: 'RESOLVED' },
];

export const mockSystemTopology = {
  nodes: [
    { id: 'res_1', type: 'Reservoir', label: '上游水库', status: { level: 150.5 }, position: { x: 100, y: 200 } },
    { id: 'pump_1', type: 'PumpStation', label: '1号泵站', status: { pump_status: 1 }, position: { x: 300, y: 100 } },
    { id: 'pump_2', type: 'PumpStation', label: '2号泵站', status: { pump_status: 0 }, position: { x: 300, y: 300 } },
    { id: 'junction_1', type: 'Junction', label: '交汇点', status: {}, position: { x: 500, y: 200 } },
    { id: 'sluice_1', type: 'SluiceGate', label: '下游闸门', status: { open: true }, position: { x: 700, y: 200 } },
  ],
  edges: [
    { from: 'res_1', to: 'pump_1' },
    { from: 'res_1', to: 'pump_2' },
    { from: 'pump_1', to: 'junction_1' },
    { from: 'pump_2', to: 'junction_1' },
    { from: 'junction_1', to: 'sluice_1' },
  ],
};

export const mockDeviceConfigs = {
  'pump_1': {
    name: '1号泵站',
    config: {
      high_pressure_threshold: 4.0,
      low_pressure_threshold: 1.5,
      communication_address: '192.168.1.101',
    }
  },
  'pump_2': {
    name: '2号泵站',
    config: {
      high_pressure_threshold: 4.2,
      low_pressure_threshold: 1.6,
      communication_address: '192.168.1.102',
    }
  },
  'sluice_1': {
    name: '下游闸门',
    config: {
      max_opening_angle: 90,
      min_opening_angle: 0,
      communication_address: '192.168.1.201',
    }
  }
};
