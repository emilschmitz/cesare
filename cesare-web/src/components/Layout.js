import React, { useState } from 'react';
import { Box, Drawer, Typography, Divider, List, ListItem, ListItemButton, ListItemText, CircularProgress, useTheme, Collapse, ListItemIcon } from '@mui/material';
import { ExpandLess, ExpandMore, Science, PlayArrow, Assessment } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Drawer width for sidebar
const drawerWidth = 280;

const Layout = ({ children, simulations, experiments, loading, selectedSimulationId }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [expandedExperiments, setExpandedExperiments] = useState({});

  // Handle simulation selection
  const handleSelectSimulation = (simulationId) => {
    navigate(`/simulations/${simulationId}`);
  };

  // Handle experiment expansion
  const handleExpandExperiment = (experimentName) => {
    setExpandedExperiments(prev => ({
      ...prev,
      [experimentName]: !prev[experimentName]
    }));
  };

  // Group simulations by experiment
  const groupedSimulations = simulations.reduce((acc, sim) => {
    const experimentName = sim.experiment_name || 'Individual Simulations';
    if (!acc[experimentName]) {
      acc[experimentName] = [];
    }
    acc[experimentName].push(sim);
    return acc;
  }, {});

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: '#343541', // Darker background like ChatGPT
              color: '#f8f9fa'  // Light text color
            },
          }}
          open
        >
          <Box sx={{ p: 2, mt: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#f8f9fa' }}>
              CESARE Dashboard
            </Typography>
          </Box>
          <Divider sx={{ backgroundColor: '#565869' }} />
          
          {/* List of experiments and simulations */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress sx={{ color: '#f8f9fa' }} />
            </Box>
          ) : (
            <List sx={{ p: 1 }}>
              {Object.keys(groupedSimulations).length > 0 ? (
                Object.entries(groupedSimulations).map(([experimentName, experimentSimulations]) => (
                  <React.Fragment key={experimentName}>
                    {/* Experiment header */}
                    <ListItem disablePadding sx={{ mb: 0.5 }}>
                      <ListItemButton 
                        onClick={() => handleExpandExperiment(experimentName)}
                        sx={{
                          borderRadius: 1,
                          '&:hover': {
                            backgroundColor: '#40414f',
                          }
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Science sx={{ color: '#f8f9fa', fontSize: '1.2rem' }} />
                        </ListItemIcon>
                        <ListItemText 
                          primary={experimentName}
                          secondary={`${experimentSimulations.length} simulation${experimentSimulations.length !== 1 ? 's' : ''}`}
                          primaryTypographyProps={{ 
                            color: '#f8f9fa',
                            fontSize: '0.9rem',
                            fontWeight: 'bold'
                          }}
                          secondaryTypographyProps={{ 
                            color: '#acacbe',
                            fontSize: '0.75rem'
                          }}
                        />
                        {expandedExperiments[experimentName] ? 
                          <ExpandLess sx={{ color: '#f8f9fa' }} /> : 
                          <ExpandMore sx={{ color: '#f8f9fa' }} />
                        }
                      </ListItemButton>
                    </ListItem>
                    
                    {/* Simulations under experiment */}
                    <Collapse in={expandedExperiments[experimentName]} timeout="auto" unmountOnExit>
                      <List component="div" disablePadding>
                        {/* Violations Summary Button for experiments (not for "Individual Simulations") */}
                        {experimentName !== 'Individual Simulations' && (
                          <ListItem disablePadding sx={{ mb: 0.5 }}>
                            <ListItemButton 
                              onClick={() => navigate(`/experiments/${encodeURIComponent(experimentName)}`)}
                              sx={{
                                borderRadius: 1,
                                ml: 2,
                                backgroundColor: '#2d2e3f',
                                '&:hover': {
                                  backgroundColor: '#40414f',
                                }
                              }}
                            >
                              <ListItemIcon sx={{ minWidth: 28 }}>
                                <Assessment sx={{ color: '#90caf9', fontSize: '1rem' }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary="Violations Summary"
                                primaryTypographyProps={{ 
                                  color: '#90caf9',
                                  fontSize: '0.85rem',
                                  fontWeight: 'bold'
                                }}
                              />
                            </ListItemButton>
                          </ListItem>
                        )}
                        
                        {experimentSimulations.map((simulation) => (
                          <ListItem key={simulation.simulation_id} disablePadding sx={{ mb: 0.5 }}>
                            <ListItemButton 
                              selected={selectedSimulationId === simulation.simulation_id}
                              onClick={() => handleSelectSimulation(simulation.simulation_id)}
                              sx={{
                                borderRadius: 1,
                                ml: 2,
                                '&.Mui-selected': {
                                  backgroundColor: '#565869',
                                  '&:hover': {
                                    backgroundColor: '#565869',
                                  }
                                },
                                '&:hover': {
                                  backgroundColor: '#40414f',
                                }
                              }}
                            >
                              <ListItemIcon sx={{ minWidth: 28 }}>
                                <PlayArrow sx={{ color: '#acacbe', fontSize: '1rem' }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={`${simulation.simulation_id.substring(0, 8)}...`}
                                secondary={`Steps: ${simulation.total_steps || 0}`}
                                primaryTypographyProps={{ 
                                  color: '#f8f9fa',
                                  fontSize: '0.85rem'
                                }}
                                secondaryTypographyProps={{ 
                                  color: '#acacbe',
                                  fontSize: '0.75rem'
                                }}
                              />
                            </ListItemButton>
                          </ListItem>
                        ))}
                      </List>
                    </Collapse>
                  </React.Fragment>
                ))
              ) : (
                <ListItem>
                  <ListItemText 
                    primary="No simulations found"
                    primaryTypographyProps={{ color: '#f8f9fa' }}
                  />
                </ListItem>
              )}
            </List>
          )}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          p: 3, 
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: theme.palette.background.default,
          height: '100vh',
          overflow: 'auto'
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout; 