import React, { useState } from 'react';
import { trainAgent } from '../services/apiService';

const TrainingModal = ({ project, onClose, onTrainingStarted }) => {
    const [algorithm, setAlgorithm] = useState('PPO');
    const [totalTimesteps, setTotalTimesteps] = useState(10000);
    const [isTraining, setIsTraining] = useState(false);
    const [error, setError] = useState('');

    const handleTrain = async (e) => {
        e.preventDefault();
        setError('');
        setIsTraining(true);

        const params = {
            algorithm,
            total_timesteps: parseInt(totalTimesteps, 10),
        };

        try {
            const result = await trainAgent(project.id, params);
            alert(`Training started successfully! Model ID: ${result.model.id}`);
            onTrainingStarted();
            onClose();
        } catch (err) {
            setError(err.message);
            alert(`Training failed: ${err.message}`);
        } finally {
            setIsTraining(false);
        }
    };

    // Basic modal styles
    const modalStyle = {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
    };

    const modalContentStyle = {
        backgroundColor: 'white',
        padding: '20px 40px',
        borderRadius: '5px',
        width: '400px',
    };

    const inputGroupStyle = {
        marginBottom: '15px',
    };

    const labelStyle = {
        display: 'block',
        marginBottom: '5px',
    };

    const inputStyle = {
        width: '100%',
        padding: '8px',
        boxSizing: 'border-box',
    };

    const buttonStyle = {
        padding: '10px 20px',
        border: 'none',
        borderRadius: '3px',
        cursor: 'pointer',
    };

    const primaryBtnStyle = { ...buttonStyle, backgroundColor: '#007bff', color: 'white' };
    const secondaryBtnStyle = { ...buttonStyle, backgroundColor: '#6c757d', color: 'white', marginRight: '10px' };


    return (
        <div style={modalStyle} onClick={onClose}>
            <div style={modalContentStyle} onClick={e => e.stopPropagation()}>
                <h2>Train Agent for {project.name}</h2>
                <form onSubmit={handleTrain}>
                    <div style={inputGroupStyle}>
                        <label style={labelStyle}>Algorithm</label>
                        <select
                            style={inputStyle}
                            value={algorithm}
                            onChange={(e) => setAlgorithm(e.target.value)}
                        >
                            <option value="PPO">PPO</option>
                            {/* Add other algorithms here in the future */}
                        </select>
                    </div>
                    <div style={inputGroupStyle}>
                        <label style={labelStyle}>Total Timesteps</label>
                        <input
                            style={inputStyle}
                            type="number"
                            value={totalTimesteps}
                            onChange={(e) => setTotalTimesteps(e.target.value)}
                        />
                    </div>
                    {error && <p style={{ color: 'red' }}>{error}</p>}
                    <div>
                        <button type="button" onClick={onClose} style={secondaryBtnStyle} disabled={isTraining}>
                            Cancel
                        </button>
                        <button type="submit" style={primaryBtnStyle} disabled={isTraining}>
                            {isTraining ? 'Training...' : 'Start Training'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TrainingModal;
