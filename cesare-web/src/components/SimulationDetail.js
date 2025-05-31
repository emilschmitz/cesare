import React from 'react';
import { Box, Typography, Paper, Divider, Tab, Tabs, CircularProgress, useTheme } from '@mui/material';
import { format } from 'date-fns';
import EthicalAnalysis from './EthicalAnalysis';
import PowerSeekingAnalysis from './PowerSeekingAnalysis';
import DisutilityAnalysis from './DisutilityAnalysis';
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
        2: 'power-seeking',
        3: 'disutility',
        4: 'configuration'
      };
      onTabChange(tabMap[newValue]);
    }
  };

  // Get the dynamic keys from simulation, with defaults for backwards compatibility
  const aiKey = simulation?.ai_key || 'instruction';
  const environmentKey = simulation?.environment_key || 'environment';

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
      case aiKey:
        return {
          bgcolor: theme.palette.messageColors.instruction.bg,
          color: theme.palette.messageColors.instruction.text,
          marginLeft: '5%',
          marginRight: '5%',
        };
      case environmentKey:
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

  // Group AI and environment responses into steps using dynamic keys
  const groupedHistory = React.useMemo(() => {
    if (!history || history.length === 0) return [];
    const result = [];
    let currentStep = null;
    history.forEach(entry => {
      if (entry.entry_type === aiKey) {
        currentStep = { instruction: entry, environment: null };
        result.push(currentStep);
      } else if (entry.entry_type === environmentKey && currentStep) {
        currentStep.environment = entry;
      }
    });
    return result;
  }, [history, aiKey, environmentKey]);
  const actualStepCount = groupedHistory.length;

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
          Steps: {actualStepCount || 0} | Instructions: {simulation.total_instructions || 0}
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
          <Tab label="Ethical Violations" id="tab-1" aria-controls="tabpanel-1" />
          <Tab label="Power Seeking" id="tab-2" aria-controls="tabpanel-2" />
          <Tab label="Disutility" id="tab-3" aria-controls="tabpanel-3" />
          <Tab label="Configuration" id="tab-4" aria-controls="tabpanel-4" />
        </Tabs>
      </Box>

      {/* Conversation tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ maxWidth: '900px', mx: 'auto' }}>
          {/* Start prompt */}
          {history && history.length > 0 && history[0].entry_type === 'start_prompt' && (
            <Paper
              key={history[0].history_id || 0}
              elevation={0}
              sx={{
                p: 2,
                mb: 3,
                backgroundColor: getMessageStyle('start_prompt').bgcolor,
                borderRadius: 2,
                marginLeft: getMessageStyle('start_prompt').marginLeft,
                marginRight: getMessageStyle('start_prompt').marginRight,
                border: '1px solid',
                borderColor: 'rgba(0,0,0,0.08)',
              }}
            >
              <Typography variant="caption" sx={{ color: getMessageStyle('start_prompt').color, opacity: 0.7, fontWeight: 500, textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.5px' }}>
                start prompt
              </Typography>
              <Typography variant="body1" sx={{ color: getMessageStyle('start_prompt').color, opacity: 0.9 }}>
                {history[0].content}
              </Typography>
            </Paper>
          )}
          {/* Grouped steps */}
          {groupedHistory.length > 0 ? (
            groupedHistory.map((step, idx) => (
              <Box key={idx} sx={{ mb: 4 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, color: theme.palette.text.secondary }}>
                  Step {idx + 1}
                </Typography>
                {/* Instruction */}
                {step.instruction && (
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      mb: 2,
                      backgroundColor: getMessageStyle(aiKey).bgcolor,
                      borderRadius: 2,
                      marginLeft: getMessageStyle(aiKey).marginLeft,
                      marginRight: getMessageStyle(aiKey).marginRight,
                      border: '1px solid',
                      borderColor: 'rgba(0,0,0,0.08)',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: getMessageStyle(aiKey).color, opacity: 0.7, fontWeight: 500, textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.5px' }}>
                      {aiKey}
                    </Typography>
                    <Typography variant="body1" sx={{ color: getMessageStyle(aiKey).color, opacity: 0.9, fontWeight: 500 }}>
                      {step.instruction.content}
                    </Typography>
                  </Paper>
                )}
                {/* Environment */}
                {step.environment && (
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      backgroundColor: getMessageStyle(environmentKey).bgcolor,
                      borderRadius: 2,
                      marginLeft: getMessageStyle(environmentKey).marginLeft,
                      marginRight: getMessageStyle(environmentKey).marginRight,
                      border: '1px solid',
                      borderColor: 'rgba(0,0,0,0.08)',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: getMessageStyle(environmentKey).color, opacity: 0.7, fontWeight: 500, textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.5px' }}>
                      {environmentKey}
                    </Typography>
                    <Typography variant="body1" sx={{ color: getMessageStyle(environmentKey).color, opacity: 0.9 }}>
                      {step.environment.content}
                    </Typography>
                  </Paper>
                )}
              </Box>
            ))
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

      {/* Power Seeking Analysis tab */}
      <TabPanel value={tabValue} index={2}>
        <PowerSeekingAnalysis
          simulationId={simulation.simulation_id}
          loading={loading}
        />
      </TabPanel>

      {/* Disutility Analysis tab */}
      <TabPanel value={tabValue} index={3}>
        <DisutilityAnalysis
          simulationId={simulation.simulation_id}
          loading={loading}
        />
      </TabPanel>

      {/* Configuration tab */}
      <TabPanel value={tabValue} index={4}>
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