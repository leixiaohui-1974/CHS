import { reactive } from 'vue';
import { useVueFlow } from '@vue-flow/core';

export default function useSimulation(elements) {
  const simulationConfig = reactive({ duration: 100, dt: 0.05 });
  const simulationState = reactive({ isRunning: false, currentTime: 0, intervalId: null });
  const { findNode } = useVueFlow();

  const runFrontendSimulation = () => {
    if (simulationState.isRunning) return;
    resetSimulationState();
    simulationState.isRunning = true;
    
    const sortedNodes = topologicalSort(elements.value);
    if (!sortedNodes) {
      alert("检测到循环依赖，无法进行仿真！");
      simulationState.isRunning = false;
      return;
    }

    simulationState.intervalId = setInterval(() => {
      if (simulationState.currentTime >= simulationConfig.duration) {
        stopSimulation();
        return;
      }

      sortedNodes.forEach(node => {
        calculateNodeOutput(node, simulationState.currentTime, simulationConfig.dt);
      });

      simulationState.currentTime += simulationConfig.dt;
    }, 20); // Faster interval for smoother visuals
  };

  const stopSimulation = () => {
    clearInterval(simulationState.intervalId);
    simulationState.isRunning = false;
  }

  const resetSimulation = () => {
    stopSimulation();
    simulationState.currentTime = 0;
    resetSimulationState();
  };
  
  const resetSimulationState = () => {
     elements.value.forEach(el => {
        if(el.data) {
            el.data.output = el.data.type === 'Reservoir' ? el.data.params.initial : 0;
            el.data.integral = 0;
            el.data.lastError = 0;
        }
    });
  };

  const topologicalSort = (graphElements) => {
    const nodes = graphElements.filter(el => el.position);
    const edges = graphElements.filter(el => el.source);
    const inDegree = new Map(nodes.map(n => [n.id, 0]));
    const adj = new Map(nodes.map(n => [n.id, []]));

    for (const edge of edges) {
      adj.get(edge.source)?.push(edge.target);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    }

    const queue = nodes.filter(n => inDegree.get(n.id) === 0);
    const result = [];

    while (queue.length > 0) {
      const u = queue.shift();
      result.push(u);
      adj.get(u.id)?.forEach(vId => {
        inDegree.set(vId, inDegree.get(vId) - 1);
        if (inDegree.get(vId) === 0) {
          const node = findNode(vId);
          if (node) queue.push(node);
        }
      });
    }

    return result.length === nodes.length ? result : null;
  };
  
  const calculateNodeOutput = (node, time, dt) => {
    const { data, id } = node;
    const { type, params } = data;
    
    const connectedEdges = elements.value.filter(el => el.target === id);
    data.inputs = {};
    connectedEdges.forEach(edge => {
      const sourceNode = findNode(edge.source);
      if (sourceNode) {
        data.inputs[edge.targetHandle || 'default'] = sourceNode.data.output || 0;
      }
    });

    switch (type) {
      case 'Constant':
        data.output = params.value || 0;
        break;
      case 'SignalGenerator':
        data.output = params.amplitude * Math.sin(2 * Math.PI * params.frequency * time);
        break;
      case 'Sum':
        const inputValues = Object.values(data.inputs);
        data.output = inputValues.reduce((sum, val) => sum + val, 0);
        break;
      case 'Reservoir':
        const inflow = data.inputs['default'] || 0;
        const currentLevel = data.output || params.initial;
        data.output = currentLevel + dt * (-params.k * currentLevel + params.k * inflow);
        break;
      case 'PIDController':
        const error = params.setpoint - (data.inputs['default'] || 0);
        data.integral = (data.integral || 0) + error * dt;
        const derivative = (error - (data.lastError || 0)) / dt;
        data.output = params.Kp * error + params.Ki * data.integral + params.Kd * derivative;
        data.lastError = error;
        break;
      case 'Dispatcher': // Mock logic
        const level = data.inputs['level'] || 0;
        if (level > params.threshold_high) data.output = 0; // stop pump
        else if (level < params.threshold_low) data.output = 1; // start pump
        else data.output = data.output; // maintain state
        break;
      case 'AIAgent': // Mock logic
        data.output = Math.random(); // Mocked AI inference
        break;
      case 'Predictor': // Mock logic
        data.output = (data.inputs['default'] || 0) * 0.95 + Math.sin(time) * 0.05; // Mocked prediction
        break;
    }
  };

  return {
    simulationConfig,
    simulationState,
    runFrontendSimulation,
    resetSimulation,
  };
}