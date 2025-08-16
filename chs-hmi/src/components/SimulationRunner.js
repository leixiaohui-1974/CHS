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
  const [formState, setFormState] = useState({
    initial_level: 19.5,
    area_storage_curve_coeff: 2000,
    width: 5,
    target_level: 20.0,
    duration_hours: 72,
  });

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormState(prevState => ({
      ...prevState,
      [name]: parseFloat(value) || 0,
    }));
  };

  const runSimulation = async (event) => {
    event.preventDefault(); // Prevent default form submission
    setLoading(true);
    setError('');
    setSimulationData(null);

    const payload = {
      scenario_name: "User Defined Test",
      components: {
        reservoir: {
          initial_level: formState.initial_level,
          area_storage_curve_coeff: formState.area_storage_curve_coeff,
        },
        sluice_gate: {
          width: formState.width,
          height: 10, // Not used by backend yet, but good to include
        },
      },
      controller: {
        type: "RuleBasedAgent",
        target_level: formState.target_level,
      },
      simulation_params: {
        duration_hours: formState.duration_hours,
      },
    };

    try {
      const response = await axios.post('/api/run_simulation', payload);
      if (response.data.status === 'success') {
        setSimulationData(response.data.data);
      } else {
        setError(response.data.message || 'An unknown error occurred.');
      }
    } catch (err) {
      if (err.response) {
        console.error("Error response:", err.response.data);
        setError(`Server Error: ${err.response.status} - ${err.response.data.message || 'Unknown error'}`);
      } else if (err.request) {
        console.error("Error request:", err.request);
        setError('No response from server. Is the backend running?');
      } else {
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
          drawOnChartArea: false,
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

  // Basic styling for the form
  const formStyle = { display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '400px', marginBottom: '20px' };
  const labelStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center' };
  const inputStyle = { padding: '5px', width: '100px' };
  const buttonStyle = { padding: '10px 20px', fontSize: '16px', cursor: 'pointer' };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>CHS-Twin-Factory: Dynamic Scenario Builder</h1>

      <form onSubmit={runSimulation} style={formStyle}>
        <h3>Scenario Editor</h3>

        <div style={labelStyle}>
          <label htmlFor="initial_level">Initial Water Level (m):</label>
          <input type="number" id="initial_level" name="initial_level" value={formState.initial_level} onChange={handleInputChange} style={inputStyle} />
        </div>

        <div style={labelStyle}>
          <label htmlFor="area_storage_curve_coeff">Reservoir Area (m²):</label>
          <input type="number" id="area_storage_curve_coeff" name="area_storage_curve_coeff" value={formState.area_storage_curve_coeff} onChange={handleInputChange} style={inputStyle} />
        </div>

        <div style={labelStyle}>
          <label htmlFor="width">Sluice Gate Width (m):</label>
          <input type="number" id="width" name="width" value={formState.width} onChange={handleInputChange} style={inputStyle} />
        </div>

        <div style={labelStyle}>
          <label htmlFor="target_level">Target Water Level (m):</label>
          <input type="number" id="target_level" name="target_level" value={formState.target_level} onChange={handleInputChange} style={inputStyle} />
        </div>

        <div style={labelStyle}>
          <label htmlFor="duration_hours">Simulation Duration (hours):</label>
          <input type="number" id="duration_hours" name="duration_hours" value={formState.duration_hours} onChange={handleInputChange} style={inputStyle} />
        </div>

        <button type="submit" disabled={loading} style={buttonStyle}>
          {loading ? 'Running Simulation...' : 'Run Simulation'}
        </button>
      </form>

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <div style={{ marginTop: '20px' }}>
        {chartData && <Line options={chartOptions} data={chartData} />}
      </div>
    </div>
  );
};

export default SimulationRunner;
