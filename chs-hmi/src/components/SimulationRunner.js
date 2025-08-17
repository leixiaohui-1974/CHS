import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
        name: '',
        initial_level: 19.5,
        area_storage_curve_coeff: 2000,
        width: 5,
        target_level: 20.0,
        duration_hours: 1,
    });

    const { id } = useParams(); // Get project ID from URL
    const navigate = useNavigate();
    const isEditing = Boolean(id);

    useEffect(() => {
        if (isEditing) {
            setLoading(true);
            axios.get(`/api/projects/${id}`)
                .then(response => {
                    const project = response.data;
                    setFormState({
                        name: project.name,
                        initial_level: project.scenario.components.reservoir.initial_level,
                        area_storage_curve_coeff: project.scenario.components.reservoir.area_storage_curve_coeff,
                        width: project.scenario.components.sluice_gate.width,
                        target_level: project.scenario.controller.target_level,
                        duration_hours: project.scenario.simulation_params.duration_hours,
                    });
                    setLoading(false);
                })
                .catch(err => {
                    setError('Failed to load project data.');
                    setLoading(false);
                });
        }
    }, [id, isEditing]);


    const handleInputChange = (event) => {
        const { name, value } = event.target;
        const isNumeric = !['name'].includes(name);
        setFormState(prevState => ({
            ...prevState,
            [name]: isNumeric ? parseFloat(value) || 0 : value,
        }));
    };

    const buildPayload = () => {
        return {
            name: formState.name,
            scenario: {
                components: {
                    reservoir: {
                        initial_level: formState.initial_level,
                        area_storage_curve_coeff: formState.area_storage_curve_coeff,
                    },
                    sluice_gate: {
                        width: formState.width,
                    },
                },
                controller: {
                    target_level: formState.target_level,
                },
                simulation_params: {
                    duration_hours: formState.duration_hours,
                },
            }
        };
    };

    const handleSaveProject = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');

        const payload = buildPayload();

        try {
            if (isEditing) {
                // To be implemented: PUT /api/projects/{id}
                // For now, we just log it.
                console.log("Would update project:", payload);
                alert("Project update successful (simulated)!");
            } else {
                await axios.post('/api/projects', payload);
                alert('Project created successfully!');
            }
            navigate('/'); // Redirect to dashboard
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to save project.');
        } finally {
            setLoading(false);
        }
    };

    const runSimulation = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');
        setSimulationData(null);

        const payload = buildPayload().scenario;

        try {
            const response = await axios.post('/api/run_simulation', payload);
            if (response.data.status === 'success') {
                setSimulationData(response.data.data);
            } else {
                setError(response.data.message || 'An unknown error occurred.');
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to run simulation.');
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
      <h1>{isEditing ? 'Edit Project' : 'Create New Project'}</h1>

      <form onSubmit={handleSaveProject} style={formStyle}>
        <h3>{isEditing ? `Editing: ${formState.name}`: 'Project Details'}</h3>

        <div style={labelStyle}>
            <label htmlFor="name">Project Name:</label>
            <input type="text" id="name" name="name" value={formState.name} onChange={handleInputChange} style={{...inputStyle, width: '250px'}} required />
        </div>

        <h3>Scenario Parameters</h3>
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

        <div style={{display: 'flex', gap: '10px', marginTop: '10px'}}>
            <button type="submit" disabled={loading} style={{...buttonStyle, backgroundColor: '#28a745'}}>
              {loading ? 'Saving...' : (isEditing ? 'Save Changes' : 'Save Project')}
            </button>
            <button type="button" onClick={runSimulation} disabled={loading} style={buttonStyle}>
              {loading ? 'Running...' : 'Run Quick Simulation'}
            </button>
        </div>
      </form>

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <div style={{ marginTop: '20px' }}>
        {chartData && <Line options={chartOptions} data={chartData} />}
      </div>
    </div>
  );
};

export default SimulationRunner;
