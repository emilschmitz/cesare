import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  ButtonGroup, 
  Collapse, 
  IconButton, 
  CircularProgress 
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import simulationsAPI from '../services/api';

const PromptsConfig = () => {
  const [activeTab, setActiveTab] = useState('simulation');
  const [prompts, setPrompts] = useState({});
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState({});
  const [error, setError] = useState(null);

  // Fetch prompts from API
  const fetchPrompts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await simulationsAPI.getPrompts();
      setPrompts(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch prompts');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch on component mount
  useEffect(() => {
    fetchPrompts();
  }, []);

  // Handle expand/collapse of a prompt
  const handleExpand = (file, key) => {
    setExpanded(prev => ({
      ...prev,
      [`${file}:${key}`]: !prev[`${file}:${key}`]
    }));
  };

  // Render prompts for a specific file
  const renderPrompts = (fileName) => {
    const filePrompts = prompts[fileName] || {};
    
    if (Object.keys(filePrompts).length === 0) {
      return <Typography variant="body1">No prompts found in {fileName}</Typography>;
    }

    return (
      <Box>
        {Object.entries(filePrompts).map(([key, value]) => (
          <Paper key={key} sx={{ mb: 2, p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                {key}
              </Typography>
              <IconButton 
                onClick={() => handleExpand(fileName, key)} 
                size="small"
              >
                {expanded[`${fileName}:${key}`] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expanded[`${fileName}:${key}`] || false}>
              <Box sx={{ mt: 1 }}>
                <Paper 
                  variant="outlined" 
                  sx={{ p: 1, background: '#f5f5f5', maxHeight: '300px', overflow: 'auto' }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {value}
                  </pre>
                </Paper>
              </Box>
            </Collapse>
          </Paper>
        ))}
      </Box>
    );
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Prompt Templates</Typography>
        <IconButton onClick={fetchPrompts} disabled={loading} size="small">
          <RefreshIcon />
        </IconButton>
      </Box>

      <ButtonGroup variant="outlined" sx={{ mb: 3 }}>
        <Button 
          onClick={() => setActiveTab('simulation')}
          variant={activeTab === 'simulation' ? 'contained' : 'outlined'}
        >
          Simulation Prompts
        </Button>
        <Button 
          onClick={() => setActiveTab('evaluation')}
          variant={activeTab === 'evaluation' ? 'contained' : 'outlined'}
        >
          Evaluation Prompts
        </Button>
      </ButtonGroup>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress size={24} />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 2, bgcolor: '#fdeaea' }}>
          <Typography color="error">Error: {error}</Typography>
        </Paper>
      ) : (
        <Box>
          {activeTab === 'simulation' && renderPrompts('prompts-simulation.yaml')}
          {activeTab === 'evaluation' && renderPrompts('prompts-evaluation.yaml')}
        </Box>
      )}
    </Box>
  );
};

export default PromptsConfig; 