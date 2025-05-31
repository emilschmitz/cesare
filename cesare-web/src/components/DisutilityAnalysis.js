import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Chip, Divider, CircularProgress, useTheme, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat, Balance } from '@mui/icons-material';
import simulationsAPI from '../services/api';

const utilityTypes = [
  { value: 1, label: 'Positive Utility', color: 'success', icon: TrendingUp, description: 'Actions that benefit, protect, or help others' },
  { value: 0, label: 'Neutral Utility', color: 'info', icon: TrendingFlat, description: 'Actions with no clear effect on others\' wellbeing' },
  { value: -1, label: 'Negative Utility (Disutility)', color: 'error', icon: TrendingDown, description: 'Actions that hurt, exploit, endanger, or disadvantage others' },
];

const DisutilityAnalysis = ({ simulationId, loading }) => {
  const theme = useTheme();
  const [disutilityData, setDisutilityData] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [utilityCounts, setUtilityCounts] = useState([]);
  const [averageUtility, setAverageUtility] = useState(0);

  // Fetch disutility data from backend
  useEffect(() => {
    if (!simulationId) return;
    
    const fetchData = async () => {
      setLoadingData(true);
      try {
        const data = await simulationsAPI.getSimulationDisutility(simulationId);
        setDisutilityData(data);

        // Calculate counts for each utility type
        const counts = utilityTypes.map(type => {
          const count = data.filter(item => item.utility_change === type.value).length;
          return { ...type, count };
        });

        setUtilityCounts(counts);

        // Calculate average utility
        if (data.length > 0) {
          const avg = data.reduce((sum, item) => sum + item.utility_change, 0) / data.length;
          setAverageUtility(avg);
        } else {
          setAverageUtility(0);
        }
      } catch (error) {
        console.error('Error fetching disutility data:', error);
        setDisutilityData([]);
        setUtilityCounts([]);
        setAverageUtility(0);
      } finally {
        setLoadingData(false);
      }
    };

    fetchData();
  }, [simulationId]);

  const UtilityIcon = ({ IconComponent, color }) => {
    return <IconComponent color={color} />;
  };

  const getUtilityType = (value) => {
    return utilityTypes.find(type => type.value === value);
  };

  const getUtilityProgressColor = (avg) => {
    if (avg > 0.1) return 'success';
    if (avg < -0.1) return 'error';
    return 'info';
  };

  if (loadingData || loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!disutilityData || disutilityData.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6">Disutility Analysis</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          No utility evaluations available for this simulation.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Utility/Disutility Analysis
      </Typography>
      
      {/* Summary section */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Utility Summary
        </Typography>
        
        <Grid container spacing={1} sx={{ mb: 3 }}>
          {utilityCounts.map((utilityType) => (
            <Grid item key={utilityType.value}>
              <Chip
                icon={<UtilityIcon IconComponent={utilityType.icon} color={utilityType.color} />}
                label={`${utilityType.label}: ${utilityType.count}`}
                color={utilityType.color}
                variant="outlined"
                sx={{ fontWeight: 'normal' }}
              />
            </Grid>
          ))}
        </Grid>

        {/* Average utility indicator */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Average Utility Change: {averageUtility.toFixed(2)}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Balance color={getUtilityProgressColor(averageUtility)} />
            <Box sx={{ flexGrow: 1 }}>
              <LinearProgress
                variant="determinate"
                value={((averageUtility + 1) / 2) * 100}
                color={getUtilityProgressColor(averageUtility)}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {averageUtility > 0 ? 'Net Positive' : averageUtility < 0 ? 'Net Negative' : 'Neutral'}
            </Typography>
          </Box>
        </Box>
        
        <Typography variant="body2" color="text.secondary">
          Total evaluations: {disutilityData.length}
        </Typography>
      </Paper>
      
      {/* Utility instances */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Utility Change Instances
        </Typography>
        
        {disutilityData.map((item, index) => {
          const utilityType = getUtilityType(item.utility_change);
          
          return (
            <Paper 
              key={item.evaluation_id || index} 
              elevation={1}
              sx={{ 
                p: 2, 
                mb: 2, 
                borderLeft: `4px solid ${theme.palette[utilityType.color].main}` 
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                <UtilityIcon IconComponent={utilityType.icon} color={utilityType.color} />
                <Box sx={{ ml: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Step {item.step}: {utilityType.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Action: {item.action}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 1 }} />
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip
                  icon={<UtilityIcon IconComponent={utilityType.icon} color={utilityType.color} />}
                  label={`Utility Change: ${item.utility_change > 0 ? '+' : ''}${item.utility_change}`}
                  color={utilityType.color}
                  size="small"
                  variant="outlined"
                />
              </Box>

              <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                Impact Description:
              </Typography>
              <Typography variant="body2" sx={{ ml: 2, fontStyle: 'italic' }}>
                {utilityType.description}
              </Typography>
            </Paper>
          );
        })}
      </Paper>
    </Box>
  );
};

export default DisutilityAnalysis; 