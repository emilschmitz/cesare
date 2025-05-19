import React from 'react';
import { Box, Typography, Paper, Divider, Tab, Tabs, CircularProgress, useTheme } from '@mui/material';
import { format } from 'date-fns';
import EthicalAnalysis from './EthicalAnalysis';
import PromptsConfig from './PromptsConfig';

// TabPanel component for tab content
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SimulationDetail = ({ simulation, history, evaluations, loading, onTabChange }) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    
    // Notify parent component about tab change if callback exists
    if (onTabChange) {
      const tabMap = {
        0: 'conversation',
        1: 'ethical-analysis',
        2: 'configuration'
      };
      onTabChange(tabMap[newValue]);
    }
  };

  // Get style based on message type with new colors and offsets
  const getMessageStyle = (type) => {
    switch (type) {
      case 'start_prompt':
        return {
          bgcolor: theme.palette.messageColors.startPrompt.bg,
          color: theme.palette.messageColors.startPrompt.text,
          marginLeft: '10%',
          marginRight: 0,
        };
      case 'instruction':
        return {
          bgcolor: theme.palette.messageColors.instruction.bg,
          color: theme.palette.messageColors.instruction.text,
          marginLeft: '5%',
          marginRight: '5%',
        };
      case 'environment':
        return {
          bgcolor: theme.palette.messageColors.environment.bg,
          color: theme.palette.messageColors.environment.text,
          marginLeft: '10%',
          marginRight: 0,
        };
      default:
        return {
          bgcolor: theme.palette.background.paper,
          color: theme.palette.text.primary,
          marginLeft: 0,
          marginRight: 0,
        };
    }
  };

  // Format date from ISO string
  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return format(new Date(dateString), 'PPp');  // Format as "Apr 29, 2021, 5:34 PM"
    } catch (error) {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!simulation) {
    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="h5">No simulation selected</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          Please select a simulation from the sidebar to view details.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Simulation header - smaller and more subtle */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ color: theme.palette.text.secondary }}>
          Simulation {simulation.simulation_id.substring(0, 8)}...
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          Started: {formatDate(simulation.start_time)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          Steps: {simulation.total_steps || 0} | Instructions: {simulation.total_instructions || 0}
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="simulation tabs"
          textColor="primary"
          indicatorColor="primary"
        >
          <Tab label="Conversation" id="tab-0" aria-controls="tabpanel-0" />
          <Tab label="Ethical Analysis" id="tab-1" aria-controls="tabpanel-1" />
          <Tab label="Configuration" id="tab-2" aria-controls="tabpanel-2" />
        </Tabs>
      </Box>

      {/* Conversation tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ maxWidth: '900px', mx: 'auto' }}>
          {history && history.length > 0 ? (
            history.map((entry, index) => {
              const style = getMessageStyle(entry.entry_type);
              
              return (
                <Paper
                  key={entry.history_id || index}
                  elevation={0}
                  sx={{
                    p: 2,
                    mb: 3,
                    backgroundColor: style.bgcolor,
                    borderRadius: 2,
                    marginLeft: style.marginLeft,
                    marginRight: style.marginRight,
                    border: '1px solid',
                    borderColor: 'rgba(0,0,0,0.08)',
                  }}
                >
                  <Box sx={{ mb: 1 }}>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        display: 'block',
                        color: style.color,
                        opacity: 0.7,
                        fontWeight: 500,
                        textTransform: 'uppercase',
                        fontSize: '0.7rem',
                        letterSpacing: '0.5px'
                      }}
                    >
                      {entry.entry_type.replace('_', ' ')}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Step {entry.step}
                    </Typography>
                  </Box>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      color: style.color,
                      opacity: 0.9,
                      fontWeight: entry.entry_type === 'instruction' ? 500 : 400
                    }}
                  >
                    {entry.content}
                  </Typography>
                </Paper>
              );
            })
          ) : (
            <Typography variant="body1">No conversation history available.</Typography>
          )}
        </Box>
      </TabPanel>

      {/* Ethical Analysis tab */}
      <TabPanel value={tabValue} index={1}>
        <EthicalAnalysis
          simulationId={simulation.simulation_id}
          evaluations={evaluations}
          loading={loading}
        />
      </TabPanel>

      {/* Configuration tab */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" sx={{ color: theme.palette.text.secondary }}>Configuration</Typography>
        
        {/* Parameters Section */}
        {simulation.config ? (
          <Paper sx={{ p: 2, mt: 2, backgroundColor: 'rgba(0,0,0,0.02)' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 500, color: theme.palette.text.secondary }}>
              Model Parameters
            </Typography>
            <pre style={{ margin: 0, padding: '10px', overflow: 'auto', fontSize: '0.9rem' }}>{JSON.stringify(simulation.config, null, 2)}</pre>
          </Paper>
        ) : (
          <Typography variant="body1">No configuration data available.</Typography>
        )}
        
        {/* Prompt Templates Section */}
        <Divider sx={{ my: 3 }} />
        <PromptsConfig />
      </TabPanel>
    </Box>
  );
};

export default SimulationDetail; 