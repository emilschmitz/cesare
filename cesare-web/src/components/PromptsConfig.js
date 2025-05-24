import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  ButtonGroup, 
  Collapse, 
  IconButton, 
  CircularProgress,
  useTheme 
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import simulationsAPI from '../services/api';

const PromptsConfig = () => {
  const theme = useTheme();
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
      return <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>No prompts found in {fileName}</Typography>;
    }

    return (
      <Box>
        {Object.entries(filePrompts).map(([key, value]) => (
          <Paper 
            key={key} 
            elevation={0}
            sx={{ 
              mb: 2, 
              p: 2, 
              backgroundColor: 'rgba(0,0,0,0.02)',
              border: '1px solid',
              borderColor: 'rgba(0,0,0,0.08)',
              borderRadius: 2,
              cursor: 'pointer',
            }}
            onClick={() => handleExpand(fileName, key)}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography 
                variant="subtitle2" 
                sx={{ 
                  fontWeight: 500, 
                  color: theme.palette.text.secondary,
                  fontSize: '0.9rem'
                }}
              >
                {key}
              </Typography>
              <IconButton 
                size="small"
                sx={{ color: theme.palette.action.active }}
                onClick={e => { e.stopPropagation(); handleExpand(fileName, key); }}
              >
                {expanded[`${fileName}:${key}`] ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              </IconButton>
            </Box>
            <Collapse in={expanded[`${fileName}:${key}`] || false}>
              <Box sx={{ mt: 1 }}>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 1, 
                    background: '#fafafa', 
                    maxHeight: '300px', 
                    overflow: 'auto',
                    border: '1px solid',
                    borderColor: 'rgba(0,0,0,0.05)',
                  }}
                >
                  <pre style={{ 
                    margin: 0, 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    color: theme.palette.text.secondary,
                    fontSize: '0.85rem' 
                  }}>
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
        <Typography variant="subtitle1" sx={{ fontWeight: 500, color: theme.palette.text.secondary }}>
          Prompt Templates
        </Typography>
        <IconButton 
          onClick={fetchPrompts} 
          disabled={loading} 
          size="small"
          sx={{ color: theme.palette.action.active }}
        >
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Box>

      <ButtonGroup 
        variant="outlined" 
        size="small"
        sx={{ 
          mb: 3,
          '& .MuiButton-root': {
            textTransform: 'none',
            color: theme.palette.text.secondary,
            borderColor: 'rgba(0,0,0,0.12)',
          },
          '& .MuiButton-contained': {
            backgroundColor: 'rgba(0,0,0,0.04)',
            fontWeight: 500,
          }
        }}
      >
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
          <CircularProgress size={20} thickness={4} sx={{ color: theme.palette.action.active }} />
        </Box>
      ) : error ? (
        <Paper 
          elevation={0}
          sx={{ 
            p: 2, 
            bgcolor: '#f9e7e7', 
            border: '1px solid',
            borderColor: '#e57373', 
            borderRadius: 1,
            color: '#b71c1c' 
          }}
        >
          <Typography variant="body2">Error: {error}</Typography>
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