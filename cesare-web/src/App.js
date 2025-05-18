import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import simulationsAPI from './services/api';
import Layout from './components/Layout';
import SimulationDetail from './components/SimulationDetail';

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb',
    },
    secondary: {
      main: '#10b981',
    },
    error: {
      main: '#ef4444',
    },
    warning: {
      main: '#f59e0b',
    },
    info: {
      main: '#3b82f6',
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
});

// SimulationView component to handle loading a single simulation
const SimulationView = () => {
  const { simulationId } = useParams();
  const [simulation, setSimulation] = useState(null);
  const [history, setHistory] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // We're acknowledging activeTab but not actively using it right now
  const [, setActiveTab] = useState('conversation');

  useEffect(() => {
    const fetchSimulationData = async () => {
      if (!simulationId) return;

      setLoading(true);
      try {
        // Fetch simulation details
        const simulationData = await simulationsAPI.getSimulation(simulationId);
        setSimulation(simulationData);

        // Fetch simulation history
        const historyData = await simulationsAPI.getSimulationHistory(simulationId);
        setHistory(historyData);

        // Fetch evaluations
        const evaluationsData = await simulationsAPI.getSimulationEvaluations(simulationId);
        setEvaluations(evaluationsData);
      } catch (error) {
        console.error('Error fetching simulation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSimulationData();
  }, [simulationId]);

  return (
    <SimulationDetail
      simulation={simulation}
      history={history}
      evaluations={evaluations}
      loading={loading}
      onTabChange={(tab) => setActiveTab(tab)}
    />
  );
};

// Main App component
function App() {
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSimulations = async () => {
      setLoading(true);
      try {
        const data = await simulationsAPI.getAllSimulations();
        setSimulations(data);
      } catch (error) {
        console.error('Error fetching simulations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSimulations();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <Layout simulations={simulations} loading={loading}>
                <div>
                  <h2>Welcome to CESARE Ethics Evaluation Dashboard</h2>
                  <p>Select a simulation from the sidebar to view details.</p>
                </div>
              </Layout>
            }
          />
          <Route
            path="/simulations/:simulationId"
            element={
              <Layout simulations={simulations} loading={loading} selectedSimulationId={window.location.pathname.split('/')[2]}>
                <SimulationView />
              </Layout>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
