import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { fetchProjectModels } from '../services/apiService';
import TrainingModal from '../components/TrainingModal';

const Dashboard = () => {
    const [projects, setProjects] = useState([]);
    const [error, setError] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedProject, setSelectedProject] = useState(null);

    const fetchProjectsAndModels = useCallback(async () => {
        try {
            const projectsResponse = await axios.get('/api/projects');
            const projectsData = projectsResponse.data;

            const projectsWithModels = await Promise.all(
                projectsData.map(async (project) => {
                    try {
                        const models = await fetchProjectModels(project.id);
                        return { ...project, models: models || [] };
                    } catch (modelError) {
                        console.error(`Failed to fetch models for project ${project.id}`, modelError);
                        return { ...project, models: [] }; // Return project without models on error
                    }
                })
            );

            setProjects(projectsWithModels);
        } catch (err) {
            setError('Failed to fetch projects. Is the backend running?');
            console.error(err);
        }
    }, []);

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

    // Styles
    const containerStyle = { fontFamily: 'sans-serif', padding: '20px', maxWidth: '900px', margin: '0 auto' };
    const headerStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #eee', paddingBottom: '10px', marginBottom: '20px' };
    const projectCardStyle = { border: '1px solid #ddd', borderRadius: '8px', padding: '20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' };
    const buttonStyle = { padding: '8px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', textDecoration: 'none', color: 'white', display: 'block', width: '100%', boxSizing: 'border-box', textAlign: 'center' };
    const createBtnStyle = { ...buttonStyle, backgroundColor: '#28a745', display: 'inline-block', width: 'auto' };
    const viewBtnStyle = { ...buttonStyle, backgroundColor: '#007bff' };
    const editBtnStyle = { ...buttonStyle, backgroundColor: '#ffc107', color: 'black' };
    const runBtnStyle = { ...buttonStyle, backgroundColor: '#17a2b8' };
    const trainBtnStyle = { ...buttonStyle, backgroundColor: '#6f42c1' };
    const downloadBtnStyle = { ...buttonStyle, backgroundColor: '#20c997', padding: '5px 10px', textDecoration: 'none', display: 'inline-block', width: 'auto' };

    return (
        <div style={containerStyle}>
            <div style={headerStyle}>
                <h1>Project Dashboard</h1>
                <Link to="/project/new" style={createBtnStyle}>Create New Project</Link>
            </div>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <div>
                {projects.length > 0 ? (
                    projects.map(project => (
                        <div key={project.id} style={projectCardStyle}>
                            <div style={{ flex: 1, marginRight: '20px' }}>
                                <h3>{project.name}</h3>
                                <div style={{ marginTop: '15px' }}>
                                    <h4>Trained Models:</h4>
                                    {project.models.length > 0 ? (
                                        <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
                                            {project.models.map(model => (
                                                <li key={model.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #eee' }}>
                                                    <div>
                                                        <div><strong>Algorithm:</strong> {model.algorithm}</div>
                                                        <div style={{fontSize: '0.8em', color: '#666'}}><strong>Trained at:</strong> {new Date(model.created_at).toLocaleString()}</div>
                                                    </div>
                                                    <a href={`/api/models/${model.id}`} style={downloadBtnStyle} download>Download</a>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p>No models trained yet.</p>
                                    )}
                                </div>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '150px' }}>
                                <button onClick={() => handleOpenTrainModal(project)} style={trainBtnStyle}>Train Agent</button>
                                <button onClick={() => handleRun(project.id)} style={runBtnStyle}>Run Sim</button>
                                <Link to={`/project/${project.id}/results`} style={viewBtnStyle}>View Results</Link>
                                <Link to={`/project/${project.id}/edit`} style={editBtnStyle}>Edit</Link>
                            </div>
                        </div>
                    ))
                ) : (
                    !error && <p>No projects found. Create one to get started!</p>
                )}
            </div>

            {isModalOpen && selectedProject && (
                <TrainingModal
                    project={selectedProject}
                    onClose={handleCloseModal}
                    onTrainingStarted={handleTrainingComplete}
                />
            )}
        </div>
    );
};

export default Dashboard;
