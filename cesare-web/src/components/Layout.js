import React from 'react';
import { Box, Drawer, AppBar, Toolbar, Typography, Divider, List, ListItem, ListItemButton, ListItemText, CircularProgress, useTheme } from '@mui/material';
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
      {/* Top App Bar */}
      <AppBar
        position="fixed"
        sx={{ 
          width: { sm: `calc(100% - ${drawerWidth}px)` }, 
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: theme.palette.primary.main
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            CESARE Ethics Evaluation Dashboard
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          <Toolbar>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Simulations
            </Typography>
          </Toolbar>
          <Divider />
          
          {/* List of simulations */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List>
              {simulations && simulations.length > 0 ? (
                simulations.map((simulation) => (
                  <ListItem key={simulation.simulation_id} disablePadding>
                    <ListItemButton 
                      selected={selectedSimulationId === simulation.simulation_id}
                      onClick={() => handleSelectSimulation(simulation.simulation_id)}
                    >
                      <ListItemText 
                        primary={`Simulation ${simulation.simulation_id.substring(0, 8)}...`}
                        secondary={`Steps: ${simulation.total_steps || 0}`}
                      />
                    </ListItemButton>
                  </ListItem>
                ))
              ) : (
                <ListItem>
                  <ListItemText primary="No simulations found" />
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
          mt: 8,
          backgroundColor: theme.palette.background.default
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout; 