import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Chip, Divider, CircularProgress, useTheme } from '@mui/material';
import { Security, BusinessCenter, Info, Groups, Extension } from '@mui/icons-material';
import simulationsAPI from '../services/api';

const powerTypes = [
  { id: 'physical_power', label: 'Physical Power', color: 'error', icon: Security, description: 'Gaining weapons, force, or ability to inflict physical damage' },
  { id: 'economic_power', label: 'Economic Power', color: 'warning', icon: BusinessCenter, description: 'Acquiring money, assets, resources, or ownership' },
  { id: 'informational_power', label: 'Informational Power', color: 'info', icon: Info, description: 'Obtaining privileged information, surveillance capabilities, or data' },
  { id: 'social_power', label: 'Social/Political Power', color: 'primary', icon: Groups, description: 'Increasing status, authority, influence over people, or control of institutions' },
  { id: 'other_power', label: 'Other Power', color: 'secondary', icon: Extension, description: 'Any other attempt to expand capacity to shape outcomes' },
];

const PowerSeekingAnalysis = ({ simulationId, loading }) => {
  const theme = useTheme();
  const [powerSeekingData, setPowerSeekingData] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [powerCounts, setPowerCounts] = useState([]);

  // Fetch power seeking data from backend
  useEffect(() => {
    if (!simulationId) return;
    
    const fetchData = async () => {
      setLoadingData(true);
      try {
        const data = await simulationsAPI.getSimulationPowerSeeking(simulationId);
        setPowerSeekingData(data);

        // Calculate counts for each power type
        const counts = powerTypes.map(type => {
          const count = data.filter(item => item[type.id]).length;
          return { ...type, count };
        }).filter(type => type.count > 0);

        setPowerCounts(counts.sort((a, b) => b.count - a.count));
      } catch (error) {
        console.error('Error fetching power seeking data:', error);
        setPowerSeekingData([]);
        setPowerCounts([]);
      } finally {
        setLoadingData(false);
      }
    };

    fetchData();
  }, [simulationId]);

  const PowerIcon = ({ IconComponent, color }) => {
    return <IconComponent color={color} />;
  };

  if (loadingData || loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!powerSeekingData || powerSeekingData.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6">Power Seeking Analysis</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          No power seeking evaluations available for this simulation.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Power Seeking Analysis
      </Typography>
      
      {/* Summary section */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Power Seeking Summary
        </Typography>
        
        <Grid container spacing={1} sx={{ mb: 2 }}>
          {powerCounts.map((powerType) => (
            <Grid item key={powerType.id}>
              <Chip
                icon={<PowerIcon IconComponent={powerType.icon} color={powerType.color} />}
                label={`${powerType.label}: ${powerType.count}`}
                color={powerType.color}
                variant="outlined"
                sx={{ fontWeight: 'normal' }}
              />
            </Grid>
          ))}
          {powerCounts.length === 0 && (
            <Grid item>
              <Chip
                label="No power seeking behaviors detected"
                color="success"
                variant="outlined"
              />
            </Grid>
          )}
        </Grid>
        
        <Typography variant="body2" color="text.secondary">
          Total evaluations: {powerSeekingData.length}
        </Typography>
      </Paper>
      
      {/* Power seeking instances */}
      {powerCounts.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
            Power Seeking Instances
          </Typography>
          
          {powerSeekingData.filter(item => 
            powerTypes.some(type => item[type.id])
          ).map((item, index) => {
            const detectedPowers = powerTypes.filter(type => item[type.id]);
            
            return (
              <Paper 
                key={item.evaluation_id || index} 
                elevation={1}
                sx={{ 
                  p: 2, 
                  mb: 2, 
                  borderLeft: `4px solid ${theme.palette.warning.main}` 
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                  <Security color="warning" />
                  <Box sx={{ ml: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      Step {item.step}: Power Seeking Behavior
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Action: {item.action}
                    </Typography>
                  </Box>
                </Box>
                
                <Divider sx={{ my: 1 }} />
                
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Detected Power Types:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {detectedPowers.map(type => (
                    <Chip 
                      key={type.id} 
                      icon={<PowerIcon IconComponent={type.icon} color={type.color} />}
                      label={type.label} 
                      size="small" 
                      color={type.color} 
                      variant="outlined" 
                    />
                  ))}
                </Box>

                {detectedPowers.length > 0 && (
                  <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      Power Type Descriptions:
                    </Typography>
                    <Box sx={{ ml: 2 }}>
                      {detectedPowers.map(type => (
                        <Typography key={type.id} variant="body2" sx={{ mb: 1 }}>
                          • <strong>{type.label}:</strong> {type.description}
                        </Typography>
                      ))}
                    </Box>
                  </>
                )}
              </Paper>
            );
          })}
        </Paper>
      )}
    </Box>
  );
};

export default PowerSeekingAnalysis; 