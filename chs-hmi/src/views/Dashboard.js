import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const Dashboard = () => {
    const [projects, setProjects] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const response = await axios.get('/api/projects');
                setProjects(response.data);
            } catch (err) {
                setError('Failed to fetch projects. Is the backend running?');
                console.error(err);
            }
        };
        fetchProjects();
    }, []);

    const containerStyle = {
        fontFamily: 'sans-serif',
        padding: '20px',
        maxWidth: '800px',
        margin: '0 auto',
    };

    const headerStyle = {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '2px solid #eee',
        paddingBottom: '10px',
        marginBottom: '20px',
    };

    const projectCardStyle = {
        border: '1px solid #ddd',
        borderRadius: '5px',
        padding: '15px',
        marginBottom: '15px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    };

    const buttonStyle = {
        padding: '8px 15px',
        margin: '0 5px',
        border: 'none',
        borderRadius: '3px',
        cursor: 'pointer',
        textDecoration: 'none',
        color: 'white',
    };

    const createBtnStyle = { ...buttonStyle, backgroundColor: '#28a745' };
    const viewBtnStyle = { ...buttonStyle, backgroundColor: '#007bff' };
    const editBtnStyle = { ...buttonStyle, backgroundColor: '#ffc107', color: 'black' };
    const runBtnStyle = { ...buttonStyle, backgroundColor: '#17a2b8' };

    const handleRun = async (projectId) => {
        try {
            alert(`Running simulation for project ${projectId}...`);
            await axios.post(`/api/projects/${projectId}/run`);
            alert(`Simulation for project ${projectId} completed!`);
            // Optionally, you could refresh the results or navigate to the results page
        } catch (err) {
            alert(`Failed to run simulation for project ${projectId}.`);
            console.error(err);
        }
    };


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
                            <h3>{project.name}</h3>
                            <div>
                                <button onClick={() => handleRun(project.id)} style={runBtnStyle}>Run</button>
                                <Link to={`/project/${project.id}/results`} style={viewBtnStyle}>View Results</Link>
                                <Link to={`/project/${project.id}/edit`} style={editBtnStyle}>Edit</Link>
                            </div>
                        </div>
                    ))
                ) : (
                    !error && <p>No projects found. Create one to get started!</p>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
