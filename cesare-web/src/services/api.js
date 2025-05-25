import axios from 'axios';

const API_URL = '/api';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
export const simulationsAPI = {
  // Get all simulations
  getAllSimulations: async () => {
    try {
      const response = await api.get('/simulations');
      return response.data;
    } catch (error) {
      console.error('Error fetching simulations:', error);
      throw error;
    }
  },

  // Get a specific simulation by ID
  getSimulation: async (simulationId) => {
    try {
      const response = await api.get(`/simulations/${simulationId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching simulation ${simulationId}:`, error);
      throw error;
    }
  },

  // Get history for a specific simulation
  getSimulationHistory: async (simulationId) => {
    try {
      const response = await api.get(`/simulations/${simulationId}/history`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching history for simulation ${simulationId}:`, error);
      throw error;
    }
  },

  // Get evaluations for a specific simulation
  getSimulationEvaluations: async (simulationId) => {
    try {
      const response = await api.get(`/simulations/${simulationId}/evaluations`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching evaluations for simulation ${simulationId}:`, error);
      throw error;
    }
  },

  // Get instructions with a specific violation type for a simulation
  getSimulationViolations: async (simulationId, violationType) => {
    try {
      const response = await api.get(`/simulations/${simulationId}/violations/${violationType}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${violationType} violations for simulation ${simulationId}:`, error);
      throw error;
    }
  },

  // Get summary of all violations
  getViolationsSummary: async () => {
    try {
      const response = await api.get('/violations/summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching violations summary:', error);
      throw error;
    }
  },
  
  // Get all prompts from YAML files
  getPrompts: async () => {
    try {
      const response = await api.get('/prompts');
      return response.data;
    } catch (error) {
      console.error('Error fetching prompts:', error);
      throw error;
    }
  },
};

// Experiments API functions
export const experimentsAPI = {
  // Get all experiments
  getAllExperiments: async () => {
    try {
      const response = await api.get('/experiments');
      return response.data;
    } catch (error) {
      console.error('Error fetching experiments:', error);
      throw error;
    }
  },

  // Get simulations for a specific experiment
  getExperimentSimulations: async (experimentName) => {
    try {
      const response = await api.get(`/experiments/${experimentName}/simulations`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching simulations for experiment ${experimentName}:`, error);
      throw error;
    }
  },

  // Get violations summary for a specific experiment
  getExperimentViolationsSummary: async (experimentName) => {
    try {
      const response = await api.get(`/experiments/${experimentName}/violations-summary`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching violations summary for experiment ${experimentName}:`, error);
      throw error;
    }
  },
};

export default simulationsAPI; 