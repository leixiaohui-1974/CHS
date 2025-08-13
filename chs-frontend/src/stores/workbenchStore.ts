import { defineStore } from 'pinia';
import { ref } from 'vue';

// Based on the 'topology.yml' structure
export interface ComponentProperty {
  [key: string]: any;
}

export interface ComponentConnection {
  [key: string]: string;
}

export interface SimulationComponent {
  name: string;
  type: string;
  properties?: ComponentProperty;
  connections?: ComponentConnection;
}

export interface SimulationConfig {
  components: SimulationComponent[];
  logging?: string[];
}

export const useWorkbenchStore = defineStore('workbench', () => {
  // The core configuration object that mirrors the YAML structure
  const config = ref<SimulationConfig>({
    components: [
      // Example initial component
      {
        name: 'inflow_to_channel',
        type: 'Disturbance',
      }
    ],
    logging: [],
  });

  // Action to add a new component to the canvas/config
  function addComponent(component: SimulationComponent) {
    const existing = config.value.components.find(c => c.name === component.name);
    if (existing) {
      console.error(`Component with name ${component.name} already exists.`);
      return;
    }
    config.value.components.push(component);
  }

  // Action to remove a component
  function removeComponent(componentName: string) {
    config.value.components = config.value.components.filter(c => c.name !== componentName);
  }

  // Action to update a component's properties or connections
  function updateComponent(componentName: string, updates: Partial<SimulationComponent>) {
    const component = config.value.components.find(c => c.name === componentName);
    if (component) {
      Object.assign(component, updates);
    }
  }

  // Action to add a connection between two components
  function addConnection(sourceComponent: string, sourcePort: string, targetComponent: string, targetPort: string) {
    const target = config.value.components.find(c => c.name === targetComponent);
    if (target) {
      if (!target.connections) {
        target.connections = {};
      }
      target.connections[targetPort] = `${sourceComponent}.${sourcePort}`;
    }
  }

  return {
    config,
    addComponent,
    removeComponent,
    updateComponent,
    addConnection,
  };
});
