import { reactive } from 'vue';
import Chart from 'chart.js/auto';

// Mock API for Backend Simulation
const mockApi = {
    _experimentState: {},

    startExperiment(model_graph, training_config) {
        console.log("Starting experiment with:", { model_graph, training_config });
        return new Promise((resolve) => {
            setTimeout(() => {
                const experiment_id = `exp_${Date.now()}`;
                this._experimentState[experiment_id] = {
                    status: 'Running',
                    step: 0,
                    reward: -1000,
                    total_timesteps: training_config.hyperparams.total_timesteps,
                };
                resolve({ experiment_id });
            }, 500);
        });
    },

    getExperimentStatus(experiment_id) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                const state = this._experimentState[experiment_id];
                if (!state) {
                    return reject(new Error("Experiment not found."));
                }

                if (state.status !== 'Running') {
                    return resolve({ status: state.status, new_logs: [], metrics: null });
                }
                
                state.step += 5000;
                state.reward += Math.random() * 100 + 50;
                const new_logs = [`[Step ${state.step}] Mean reward: ${state.reward.toFixed(2)}`];
                
                if (state.step >= state.total_timesteps) {
                    state.status = 'Completed';
                    new_logs.push('Training finished successfully.');
                }

                resolve({
                    status: state.status,
                    new_logs,
                    metrics: {
                        step: state.step,
                        reward: state.reward
                    }
                });

            }, 1000);
        });
    }
};

export default function useAITraining(modelGraph, chartCanvasRef) {
  const trainingConfig = reactive({
    name: 'Test Experiment',
    algorithm: 'PPO',
    hyperparams: {
      learning_rate: 0.0003,
      total_timesteps: 100000,
    }
  });

  const trainingState = reactive({
    isRunning: false,
    experimentId: null,
    logs: [],
    intervalId: null,
  });

  let chartInstance = null;

  const initializeChart = () => {
    if (chartCanvasRef.value && !chartInstance) {
      const ctx = chartCanvasRef.value.getContext('2d');
      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Reward',
            data: [],
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: 'Step' } },
            y: { title: { display: true, text: 'Reward' } }
          }
        }
      });
    }
  };

  const updateChart = (step, reward) => {
    if (chartInstance) {
      chartInstance.data.labels.push(step);
      chartInstance.data.datasets[0].data.push(reward);
      chartInstance.update();
    }
  };

  const resetChart = () => {
    if (chartInstance) {
      chartInstance.data.labels = [];
      chartInstance.data.datasets[0].data = [];
      chartInstance.update();
    }
  };

  const startBackendTraining = async () => {
    trainingState.isRunning = true;
    trainingState.logs = ['Serializing model graph...'];
    resetChart();

    try {
      const response = await mockApi.startExperiment(modelGraph, trainingConfig);
      trainingState.experimentId = response.experiment_id;
      trainingState.logs.push(`Experiment ${response.experiment_id} started.`);
      trainingState.intervalId = setInterval(monitorTraining, 2000);
    } catch (error) {
      trainingState.logs.push(`Error: ${error.message}`);
      trainingState.isRunning = false;
    }
  };

  const monitorTraining = async () => {
    if (!trainingState.isRunning || !trainingState.experimentId) {
      clearInterval(trainingState.intervalId);
      return;
    }
    try {
      const status = await mockApi.getExperimentStatus(trainingState.experimentId);
      
      status.new_logs.forEach(log => trainingState.logs.push(log));
      if (trainingState.logs.length > 50) {
        trainingState.logs.splice(0, trainingState.logs.length - 50);
      }

      if (status.metrics) {
        updateChart(status.metrics.step, status.metrics.reward);
      }

      if (status.status === 'Completed' || status.status === 'Failed') {
        trainingState.isRunning = false;
        trainingState.logs.push(`Training ${status.status}.`);
        clearInterval(trainingState.intervalId);
      }
    } catch (error) {
      trainingState.logs.push(`Monitor Error: ${error.message}`);
      trainingState.isRunning = false;
      clearInterval(trainingState.intervalId);
    }
  };

  return {
    trainingConfig,
    trainingState,
    startBackendTraining,
    initializeChart,
  };
}