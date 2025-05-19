import React from 'react';
import { Box, Typography, Paper, Divider, Avatar, Tab, Tabs, CircularProgress, useTheme } from '@mui/material';
import { Person, Android, Info } from '@mui/icons-material';
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

  // Get avatar and style based on message type
  const getMessageStyle = (type) => {
    switch (type) {
      case 'start_prompt':
        return {
          avatar: <Info color="primary" />,
          bgcolor: theme.palette.info.light + '33',  // Adding transparency
          color: theme.palette.info.dark,
        };
      case 'instruction':
        return {
          avatar: <Person color="primary" />,
          bgcolor: theme.palette.primary.light + '33',
          color: theme.palette.primary.dark,
        };
      case 'environment':
        return {
          avatar: <Android color="secondary" />,
          bgcolor: theme.palette.secondary.light + '33',
          color: theme.palette.secondary.dark,
        };
      default:
        return {
          avatar: <Info color="default" />,
          bgcolor: theme.palette.grey[200],
          color: theme.palette.grey[800],
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
      {/* Simulation header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          Simulation Details
        </Typography>
        <Typography variant="body2" color="text.secondary">
          ID: {simulation.simulation_id}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Start Time: {formatDate(simulation.start_time)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Steps: {simulation.total_steps || 0} | Instructions: {simulation.total_instructions || 0}
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="simulation tabs">
          <Tab label="Conversation" id="tab-0" aria-controls="tabpanel-0" />
          <Tab label="Ethical Analysis" id="tab-1" aria-controls="tabpanel-1" />
          <Tab label="Configuration" id="tab-2" aria-controls="tabpanel-2" />
        </Tabs>
      </Box>

      {/* Conversation tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
          {history && history.length > 0 ? (
            history.map((entry, index) => {
              const style = getMessageStyle(entry.entry_type);
              
              return (
                <Paper
                  key={entry.history_id || index}
                  elevation={1}
                  sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: style.bgcolor,
                    borderRadius: 2,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Avatar sx={{ bgcolor: style.color, mr: 1 }}>
                      {style.avatar}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: style.color }}>
                        {entry.entry_type.charAt(0).toUpperCase() + entry.entry_type.slice(1)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Step {entry.step}
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
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
        <Typography variant="h6">Configuration</Typography>
        
        {/* Parameters Section */}
        {simulation.config ? (
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              Model Parameters
            </Typography>
            <pre>{JSON.stringify(simulation.config, null, 2)}</pre>
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