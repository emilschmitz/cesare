import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, Chip, Divider, Button, FormControl, InputLabel, MenuItem, Select, CircularProgress, useTheme } from '@mui/material';
import { WarningAmber, ErrorOutline, CheckCircleOutline } from '@mui/icons-material';
import simulationsAPI from '../services/api';

const violationTypes = [
  { id: 'killing', label: 'Killing', color: 'error', severity: 3 },
  { id: 'physical_harm', label: 'Physical Harm', color: 'error', severity: 3 },
  { id: 'non_physical_harm', label: 'Non-Physical Harm', color: 'error', severity: 2 },
  { id: 'intending_harm', label: 'Intending Harm', color: 'warning', severity: 2 },
  { id: 'deception', label: 'Deception', color: 'warning', severity: 2 },
  { id: 'manipulation', label: 'Manipulation', color: 'warning', severity: 2 },
  { id: 'betrayal', label: 'Betrayal', color: 'warning', severity: 2 },
  { id: 'stealing', label: 'Stealing', color: 'warning', severity: 1 },
  { id: 'trespassing', label: 'Trespassing', color: 'warning', severity: 1 },
  { id: 'spying', label: 'Spying', color: 'warning', severity: 1 },
  { id: 'vandalism', label: 'Vandalism', color: 'warning', severity: 1 },
  { id: 'unfairness', label: 'Unfairness', color: 'warning', severity: 1 },
  { id: 'other', label: 'Other', color: 'info', severity: 1 },
];

const EthicalAnalysis = ({ simulationId, loading }) => {
  const theme = useTheme();
  const [selectedViolation, setSelectedViolation] = useState('');
  const [filteredViolations, setFilteredViolations] = useState([]);
  const [loadingViolations, setLoadingViolations] = useState(false);
  const [violationCounts, setViolationCounts] = useState([]);
  const [loadingCounts, setLoadingCounts] = useState(false);
  const [ethicalViolationsData, setEthicalViolationsData] = useState([]);

  // Fetch ethical violations data from backend
  useEffect(() => {
    if (!simulationId) return;
    
    const fetchData = async () => {
      try {
        const data = await simulationsAPI.getSimulationEthicalViolations(simulationId);
        setEthicalViolationsData(data);
      } catch (error) {
        console.error('Error fetching ethical violations data:', error);
        setEthicalViolationsData([]);
      }
    };

    fetchData();
  }, [simulationId]);

  // Fetch violation counts from backend for each type
  useEffect(() => {
    if (!simulationId) return;
    let isMounted = true;
    setLoadingCounts(true);
    Promise.all(
      violationTypes.map(async (type) => {
        try {
          const data = await simulationsAPI.getSimulationViolations(simulationId, type.id);
          return { ...type, count: data.length };
        } catch {
          return { ...type, count: 0 };
        }
      })
    ).then((results) => {
      if (isMounted) {
        setViolationCounts(results.filter(type => type.count > 0).sort((a, b) => b.count - a.count));
        setLoadingCounts(false);
      }
    });
    return () => { isMounted = false; };
  }, [simulationId]);

  useEffect(() => {
    if (selectedViolation && simulationId) {
      fetchViolations();
    } else {
      setFilteredViolations([]);
    }
  }, [selectedViolation, simulationId]);

  const fetchViolations = async () => {
    if (!selectedViolation) return;
    
    setLoadingViolations(true);
    try {
      const data = await simulationsAPI.getSimulationViolations(simulationId, selectedViolation);
      setFilteredViolations(data);
    } catch (error) {
      console.error('Error fetching violations:', error);
      setFilteredViolations([]);
    } finally {
      setLoadingViolations(false);
    }
  };

  const handleViolationTypeChange = (event) => {
    setSelectedViolation(event.target.value);
  };

  const ViolationIcon = ({ severity }) => {
    switch (severity) {
      case 3:
        return <ErrorOutline color="error" />;
      case 2:
        return <WarningAmber color="warning" />;
      default:
        return <WarningAmber color="info" />;
    }
  };

  // If there are no evaluations
  if (!ethicalViolationsData || ethicalViolationsData.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6">Ethical Analysis</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          No ethical evaluations available for this simulation.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Ethical Violations Analysis
      </Typography>
      
      {/* Summary section */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Violations Summary
        </Typography>
        
        <Grid container spacing={1} sx={{ mb: 2 }}>
          {loadingCounts ? (
            <Grid item><CircularProgress size={18} /></Grid>
          ) : (
            violationCounts.map((violation) => (
              <Grid item key={violation.id}>
                <Chip
                  icon={<ViolationIcon severity={violation.severity} />}
                  label={`${violation.label}: ${violation.count}`}
                  color={violation.color}
                  variant="outlined"
                  clickable
                  onClick={() => setSelectedViolation(violation.id)}
                  sx={{ 
                    fontWeight: selectedViolation === violation.id ? 'bold' : 'normal',
                    border: selectedViolation === violation.id ? 2 : 1
                  }}
                />
              </Grid>
            ))
          )}
        </Grid>
        
        <Typography variant="body2" color="text.secondary">
          Total evaluations: {ethicalViolationsData.length}
        </Typography>
      </Paper>
      
      {/* Filter section */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Filter Violations
        </Typography>
        
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small" sx={{ minWidth: selectedViolation ? undefined : 220 }}>
              <InputLabel id="violation-type-label">Violation Type</InputLabel>
              <Select
                labelId="violation-type-label"
                id="violation-type-select"
                value={selectedViolation}
                label="Violation Type"
                onChange={handleViolationTypeChange}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 300,
                      width: 250,
                    },
                  },
                }}
              >
                <MenuItem value="">
                  <em>None</em>
                </MenuItem>
                {violationCounts.map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    {type.label} ({type.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item>
            <Button 
              variant="outlined" 
              onClick={fetchViolations}
              disabled={!selectedViolation || loadingViolations}
            >
              Apply Filter
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Results section */}
      {selectedViolation ? (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
            {selectedViolation && `${violationTypes.find(v => v.id === selectedViolation)?.label || selectedViolation} Violations`}
          </Typography>
          
          {loadingViolations ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {filteredViolations.length > 0 ? (
                <Box>
                  {filteredViolations.map((violation, index) => {
                    const violationType = violationTypes.find(v => v.id === selectedViolation);
                    
                    return (
                      <Paper 
                        key={violation.evaluation_id || index} 
                        elevation={1}
                        sx={{ 
                          p: 2, 
                          mb: 2, 
                          borderLeft: `4px solid ${theme.palette[violationType?.color || 'warning'].main}` 
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                          <ViolationIcon severity={violationType?.severity || 1} />
                          <Box sx={{ ml: 1 }}>
                            <Typography variant="subtitle2" fontWeight="bold">
                              Step {violation.step}: {violationType?.label || selectedViolation} Violation
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Action: {violation.action}
                            </Typography>
                          </Box>
                        </Box>
                        
                        <Divider sx={{ my: 1 }} />
                        
                        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          Instruction:
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                          {violation.instruction_content}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          Detected Violations:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {violationTypes.filter(type => violation[type.id]).map(type => (
                            <Chip 
                              key={type.id} 
                              label={type.label} 
                              size="small" 
                              color={type.color} 
                              variant="outlined" 
                            />
                          ))}
                        </Box>
                      </Paper>
                    );
                  })}
                </Box>
              ) : (
                <Typography variant="body1">
                  No {selectedViolation} violations found in this simulation.
                </Typography>
              )}
            </>
          )}
        </Paper>
      ) : (
        <Typography variant="body1" sx={{ mt: 2 }}>
          Select a violation type to see details.
        </Typography>
      )}
    </Box>
  );
};

export default EthicalAnalysis; 