import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import simulationsAPI, { experimentsAPI } from './services/api';
import Layout from './components/Layout';
import SimulationDetail from './components/SimulationDetail';

// Create a theme instance with natural colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#546e7a', // Bluish-gray
    },
    secondary: {
      main: '#78909c', // Lighter bluish-gray
    },
    error: {
      main: '#b71c1c', // Dark red
    },
    warning: {
      main: '#e57373', // Light red
    },
    info: {
      main: '#90a4ae', // Light bluish-gray
    },
    background: {
      default: '#f5f5f5', // Light gray
      paper: '#ffffff', // White for paper components
    },
    messageColors: {
      startPrompt: {
        bg: '#fff8e1', // Soft orange pastel
        text: '#bf8c64', // Darker orange brown for text
      },
      instruction: {
        bg: '#f5f5f5', // Light gray
        text: '#424242', // Dark gray for text
      },
      environment: {
        bg: '#e8f5e9', // Soft green pastel
        text: '#558b2f', // Natural green for text
      },
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
});

// LayoutWrapper to get current location/params and pass to Layout
const LayoutWrapper = ({ children, simulations, experiments, loading }) => {
  const location = useLocation();
  const simulationId = location.pathname.split('/')[2]; // Extract simulationId from URL

  return (
    <Layout 
      simulations={simulations} 
      experiments={experiments}
      loading={loading} 
      selectedSimulationId={simulationId}
    >
      {children}
    </Layout>
  );
};

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
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch simulations and experiments in parallel
        const [simulationsData, experimentsData] = await Promise.all([
          simulationsAPI.getAllSimulations(),
          experimentsAPI.getAllExperiments()
        ]);
        
        setSimulations(simulationsData);
        setExperiments(experimentsData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <LayoutWrapper simulations={simulations} experiments={experiments} loading={loading}>
                <div>
                  <h2>Welcome to CESARE Ethics Evaluation Dashboard</h2>
                  <p>Select a simulation from the sidebar to view details.</p>
                </div>
              </LayoutWrapper>
            }
          />
          <Route
            path="/simulations/:simulationId"
            element={
              <LayoutWrapper simulations={simulations} experiments={experiments} loading={loading}>
                <SimulationView />
              </LayoutWrapper>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
