import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Line } from 'react-chartjs-2';

const ResultViewer = () => {
    const [runs, setRuns] = useState([]);
    const [selectedRuns, setSelectedRuns] = useState([]);
    const [chartData, setChartData] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { id: projectId } = useParams();

    useEffect(() => {
        setLoading(true);
        axios.get(`/api/projects/${projectId}/runs`)
            .then(response => {
                setRuns(response.data);
                setLoading(false);
            })
            .catch(err => {
                setError('Failed to load simulation runs.');
                setLoading(false);
            });
    }, [projectId]);

    const handleRunSelection = (runId) => {
        setSelectedRuns(prevSelected =>
            prevSelected.includes(runId)
                ? prevSelected.filter(id => id !== runId)
                : [...prevSelected, runId]
        );
    };

    const colors = ['rgb(53, 162, 235)', 'rgb(255, 99, 132)', 'rgb(75, 192, 192)', 'rgb(255, 205, 86)', 'rgb(153, 102, 255)'];

    useEffect(() => {
        if (selectedRuns.length > 0) {
            const datasets = selectedRuns.flatMap((runId, index) => {
                const run = runs.find(r => r.id === runId);
                if (!run) return [];

                const color = colors[index % colors.length];
                const runLabel = new Date(run.run_timestamp).toLocaleString();

                return [{
                    label: `Level - ${runLabel}`,
                    data: run.results.level,
                    borderColor: color,
                    backgroundColor: `${color.slice(0, -1)}, 0.5)`, // Make transparent
                    yAxisID: 'y',
                }];
            });

            // Assume all runs have the same time labels
            const firstSelectedRun = runs.find(r => r.id === selectedRuns[0]);
            const labels = firstSelectedRun ? firstSelectedRun.results.time : [];

            setChartData({
                labels,
                datasets,
            });
        } else {
            setChartData(null);
        }
    }, [selectedRuns, runs]);


    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Simulation Results Comparison' },
        },
        scales: {
            y: {
                display: true,
                title: { display: true, text: 'Level (m)' },
            },
        },
    };

    const containerStyle = { fontFamily: 'sans-serif', padding: '20px' };
    const listStyle = { listStyle: 'none', padding: 0 };
    const itemStyle = { border: '1px solid #ddd', borderRadius: '4px', marginBottom: '5px', padding: '10px' };

    return (
        <div style={containerStyle}>
            <h1>Simulation Results for Project {projectId}</h1>
            {loading && <p>Loading runs...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <h3>Select runs to compare:</h3>
            <ul style={listStyle}>
                {runs.map(run => (
                    <li key={run.id} style={itemStyle}>
                        <label>
                            <input
                                type="checkbox"
                                checked={selectedRuns.includes(run.id)}
                                onChange={() => handleRunSelection(run.id)}
                            />
                            Run from {new Date(run.run_timestamp).toLocaleString()}
                        </label>
                    </li>
                ))}
            </ul>

            <div style={{ marginTop: '20px' }}>
                {chartData ? (
                    <Line options={chartOptions} data={chartData} />
                ) : (
                    <p>Select one or more runs to see the comparison chart.</p>
                )}
            </div>
        </div>
    );
};

export default ResultViewer;
