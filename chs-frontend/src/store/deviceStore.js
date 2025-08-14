import { defineStore } from 'pinia';

export const useDeviceStore = defineStore('device', {
  state: () => ({
    devices: [
      { id: 'dev-001', name: '1号泵站控制器', ip: '192.168.1.10', role: 'Pump Controller', status: 'Online' },
      { id: 'dev-002', name: '2号闸门感知器', ip: '192.168.1.11', role: 'Gate Sensor', status: 'Offline' },
      { id: 'dev-003', name: '3号备用控制器', ip: '192.168.1.12', role: 'Unassigned', status: 'Online' },
    ],
  }),
  actions: {
    async registerDevice(device) {
      const newDevice = { ...device, id: `dev-${Date.now()}`, status: 'Unknown' };
      this.devices.push(newDevice);
    },
  },
});
