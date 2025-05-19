import React from 'react';
import { Box, Drawer, Typography, Divider, List, ListItem, ListItemButton, ListItemText, CircularProgress, useTheme } from '@mui/material';
import { useNavigate } from 'react-router-dom';

// Drawer width for sidebar
const drawerWidth = 280;

const Layout = ({ children, simulations, loading, selectedSimulationId }) => {
  const theme = useTheme();
  const navigate = useNavigate();

  // Handle simulation selection
  const handleSelectSimulation = (simulationId) => {
    navigate(`/simulations/${simulationId}`);
  };

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
              Simulations
            </Typography>
          </Box>
          <Divider sx={{ backgroundColor: '#565869' }} />
          
          {/* List of simulations */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress sx={{ color: '#f8f9fa' }} />
            </Box>
          ) : (
            <List sx={{ p: 1 }}>
              {simulations && simulations.length > 0 ? (
                simulations.map((simulation) => (
                  <ListItem key={simulation.simulation_id} disablePadding sx={{ mb: 1 }}>
                    <ListItemButton 
                      selected={selectedSimulationId === simulation.simulation_id}
                      onClick={() => handleSelectSimulation(simulation.simulation_id)}
                      sx={{
                        borderRadius: 1,
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
                      <ListItemText 
                        primary={`Simulation ${simulation.simulation_id.substring(0, 8)}...`}
                        secondary={`Steps: ${simulation.total_steps || 0}`}
                        primaryTypographyProps={{ 
                          color: '#f8f9fa',
                          fontSize: '0.9rem'
                        }}
                        secondaryTypographyProps={{ 
                          color: '#acacbe',
                          fontSize: '0.8rem'
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
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