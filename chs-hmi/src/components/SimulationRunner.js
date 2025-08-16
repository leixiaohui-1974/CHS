import React, { useState } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const SimulationRunner = () => {
  const [simulationData, setSimulationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    setSimulationData(null);
    try {
      // With the proxy in package.json, we can use a relative path
      const response = await axios.post('/api/run_simulation');
      if (response.data.status === 'success') {
        setSimulationData(response.data.data);
      } else {
        setError(response.data.message || 'An unknown error occurred.');
      }
    } catch (err) {
      if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error("Error response:", err.response.data);
        setError(`Server Error: ${err.response.status} - ${err.response.data.message || 'Unknown error'}`);
      } else if (err.request) {
        // The request was made but no response was received
        console.error("Error request:", err.request);
        setError('No response from server. Is the backend running?');
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error', err.message);
        setError(`Request Error: ${err.message}`);
      }
      console.error("Full error object:", err);
    } finally {
      setLoading(false);
    }
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Simulation Results',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        display: true,
        title: {
          display: true,
          text: 'Level (m)',
        },
      },
      y1: {
        beginAtZero: true,
        type: 'linear',
        position: 'right',
        display: true,
        title: {
          display: true,
          text: 'Flow (m³/s)',
        },
        grid: {
          drawOnChartArea: false, // only draw grid for the first Y axis
        },
      },
    },
  };

  const chartData = simulationData ? {
    labels: simulationData.time,
    datasets: [
      {
        label: 'Reservoir Level',
        data: simulationData.level,
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        yAxisID: 'y',
      },
      {
        label: 'Inflow',
        data: simulationData.inflow,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        yAxisID: 'y1',
      },
      {
        label: 'Outflow',
        data: simulationData.outflow,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        yAxisID: 'y1',
      },
    ],
  } : null;

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>CHS-Twin-Factory MVP</h1>
      <button onClick={runSimulation} disabled={loading} style={{ padding: '10px 20px', fontSize: '16px' }}>
        {loading ? 'Running Simulation...' : 'Run Simulation'}
      </button>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <div style={{ marginTop: '20px' }}>
        {chartData && <Line options={chartOptions} data={chartData} />}
      </div>
    </div>
  );
};

export default SimulationRunner;
