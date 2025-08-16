import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './views/Dashboard';
import SimulationRunner from './components/SimulationRunner'; // Re-using this for project creation/editing
import './App.css';

// A simple wrapper for the project editor/creator
const ProjectEditor = () => (
    <div>
        <h1 style={{ textAlign: 'center' }}>Create/Edit Project</h1>
        <SimulationRunner />
    </div>
);

import ResultViewer from './views/ResultViewer';


function App() {
  return (
    <Router>
        <div className="App">
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/project/new" element={<ProjectEditor />} />
                <Route path="/project/:id/edit" element={<ProjectEditor />} />
                <Route path="/project/:id/results" element={<ResultViewer />} />
            </Routes>
        </div>
    </Router>
  );
}

export default App;
