import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Box,
  Card,
  CardContent,
  Grid,
  Button,
  Tooltip,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { Download, ExpandMore } from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

const ExperimentEthicalAnalysis = () => {
  const { experimentName } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/experiments/${experimentName}/violations-summary`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [experimentName]);

  const violationTypes = [
    'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
    'deception', 'manipulation', 'betrayal', 'stealing',
    'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
  ];

  const formatViolationType = (type) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const generateCSV = () => {
    if (!data || !data.aggregated_stats) return '';

    const headers = [
      'Agent Model',
      'Total Simulations',
      'Total Instructions',
      'Avg Instructions/Sim',
      'Positive Utility %',
      'Neutral Utility %', 
      'Negative Utility %',
      'Avg Net Utility/Sim',
      'Net Utility Std Dev',
      'Avg Utility/Sim',
      ...violationTypes.map(type => `${formatViolationType(type)} %`)
    ];

    const csvContent = [
      headers.join(','),
      ...data.aggregated_stats.map(stat => [
        `"${stat.agent_model}"`,
        stat.total_simulations,
        stat.total_instructions,
        stat.avg_instructions_per_simulation.toFixed(1),
        stat.positive_utility_percentage.toFixed(2),
        stat.neutral_utility_percentage.toFixed(2),
        stat.negative_utility_percentage.toFixed(2),
        stat.avg_net_utility_per_simulation,
        stat.net_utility_std_dev,
        stat.avg_utility_per_simulation,
        ...violationTypes.map(type => stat[`${type}_percentage`].toFixed(3))
      ].join(','))
    ].join('\\n');

    return csvContent;
  };

  const downloadCSV = () => {
    const csvContent = generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${experimentName}_ethical_analysis.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const generateMarkdown = () => {
    if (!data || !data.aggregated_stats) return '';

    let markdown = `# Ethical Analysis Summary: ${experimentName}\\n\\n`;
    markdown += `**Total Simulations:** ${data.total_simulations}\\n\\n`;

    // Aggregated Statistics Table
    markdown += '## Aggregated Statistics by Agent Model\\n\\n';
    markdown += '| Agent Model | Sims | Instructions | Pos Util % | Neg Util % | Net Util Avg | Net Util Std Dev |';
    violationTypes.forEach(type => {
      markdown += ` ${formatViolationType(type)} % |`;
    });
    markdown += '\\n';

    markdown += '|-------------|------|-------------|-----------|-----------|-------------|-----------------|';
    violationTypes.forEach(() => {
      markdown += '----------|';
    });
    markdown += '\\n';

    data.aggregated_stats.forEach(stat => {
      const modelName = stat.agent_model;
      markdown += `| ${modelName} | ${stat.total_simulations} | ${stat.total_instructions} | ${stat.positive_utility_percentage.toFixed(1)}% | ${stat.negative_utility_percentage.toFixed(1)}% | ${stat.avg_net_utility_per_simulation} | ${stat.net_utility_std_dev} |`;
      violationTypes.forEach(type => {
        markdown += ` ${stat[`${type}_percentage`].toFixed(2)}% |`;
      });
      markdown += '\\n';
    });

    return markdown;
  };

  const downloadMarkdown = () => {
    const markdownContent = generateMarkdown();
    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${experimentName}_ethical_analysis.md`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Error loading ethical analysis: {error}</Alert>
      </Container>
    );
  }

  if (!data || !data.aggregated_stats || data.aggregated_stats.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">No ethical analysis data available for this experiment.</Alert>
      </Container>
    );
  }

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Prepare chart data for violations
  const violationChartData = data.aggregated_stats.map(stat => ({
    name: stat.agent_model.length > 20 ? stat.agent_model.substring(0, 20) + '...' : stat.agent_model,
    ...violationTypes.reduce((acc, type) => {
      acc[formatViolationType(type)] = stat[`${type}_percentage`];
      return acc;
    }, {})
  }));

  // Prepare chart data for utility
  const utilityChartData = data.aggregated_stats.map(stat => ({
    name: stat.agent_model.length > 20 ? stat.agent_model.substring(0, 20) + '...' : stat.agent_model,
    'Positive Utility %': stat.positive_utility_percentage,
    'Neutral Utility %': stat.neutral_utility_percentage,
    'Negative Utility %': stat.negative_utility_percentage,
    'Net Utility Avg': stat.avg_net_utility_per_simulation
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Ethical Analysis: {experimentName}
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={downloadCSV}
              sx={{ mr: 1 }}
            >
              Download CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={downloadMarkdown}
            >
              Download MD
            </Button>
          </Box>
        </Box>

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
          <Tab label="Aggregated Statistics" />
          <Tab label="Individual Simulations" />
          <Tab label="Visualizations" />
        </Tabs>

        {tabValue === 0 && (
          <Box>
            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Agent Configurations
                    </Typography>
                    <Typography variant="h4">
                      {data.aggregated_stats.length}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Simulations
                    </Typography>
                    <Typography variant="h4">
                      {data.total_simulations}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Total Instructions
                    </Typography>
                    <Typography variant="h4">
                      {data.aggregated_stats.reduce((sum, stat) => sum + stat.total_instructions, 0)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Avg Instructions/Sim
                    </Typography>
                    <Typography variant="h4">
                      {(data.aggregated_stats.reduce((sum, stat) => sum + stat.avg_instructions_per_simulation, 0) / data.aggregated_stats.length).toFixed(1)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Aggregated Statistics Table */}
            <TableContainer component={Paper} sx={{ mb: 4 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Agent Model</strong></TableCell>
                    <TableCell align="center"><strong>Simulations</strong></TableCell>
                    <TableCell align="center"><strong>Instructions</strong></TableCell>
                    <TableCell align="center"><strong>Positive Utility %</strong></TableCell>
                    <TableCell align="center"><strong>Negative Utility %</strong></TableCell>
                    <TableCell align="center"><strong>Net Utility Avg</strong></TableCell>
                    <TableCell align="center"><strong>Net Utility Std Dev</strong></TableCell>
                    {violationTypes.map(type => (
                      <TableCell key={type} align="center">
                        <strong>{formatViolationType(type)} %</strong>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.aggregated_stats.map((stat, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Tooltip title={stat.agent_model}>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {stat.agent_model.length > 30 ? stat.agent_model.substring(0, 30) + '...' : stat.agent_model}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">{stat.total_simulations}</TableCell>
                      <TableCell align="center">{stat.total_instructions}</TableCell>
                      <TableCell align="center" sx={{ color: 'green' }}>
                        {stat.positive_utility_percentage.toFixed(1)}%
                      </TableCell>
                      <TableCell align="center" sx={{ color: 'red' }}>
                        {stat.negative_utility_percentage.toFixed(1)}%
                      </TableCell>
                      <TableCell align="center" sx={{ color: stat.avg_net_utility_per_simulation >= 0 ? 'green' : 'red' }}>
                        {stat.avg_net_utility_per_simulation}
                      </TableCell>
                      <TableCell align="center">{stat.net_utility_std_dev}</TableCell>
                      {violationTypes.map(type => (
                        <TableCell key={type} align="center">
                          {stat[`${type}_percentage`].toFixed(2)}%
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {tabValue === 1 && (
          <Box>
            {/* Individual Simulations */}
            {data.aggregated_stats.map((agentStat, agentIndex) => (
              <Accordion key={agentIndex} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    {agentStat.agent_model} ({agentStat.total_simulations} simulations)
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Simulation ID</strong></TableCell>
                          <TableCell align="center"><strong>Repetition</strong></TableCell>
                          <TableCell align="center"><strong>Steps</strong></TableCell>
                          <TableCell align="center"><strong>Instructions</strong></TableCell>
                          <TableCell align="center"><strong>Total Violations</strong></TableCell>
                          <TableCell align="center"><strong>Net Utility</strong></TableCell>
                          <TableCell align="center"><strong>Ethical Risk</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {agentStat.simulations.map((sim, simIndex) => (
                          <TableRow key={simIndex} hover>
                            <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                              {sim.simulation_id.substring(0, 8)}...
                            </TableCell>
                            <TableCell align="center">{sim.repetition}/{sim.total_repetitions}</TableCell>
                            <TableCell align="center">{sim.total_steps}</TableCell>
                            <TableCell align="center">{sim.total_instructions}</TableCell>
                            <TableCell align="center">{sim.total_violations}</TableCell>
                            <TableCell align="center" sx={{ color: sim.net_utility >= 0 ? 'green' : 'red' }}>
                              {sim.net_utility}
                            </TableCell>
                            <TableCell align="center">{sim.ethical_risk_score}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {tabValue === 2 && (
          <Box>
            {/* Visualizations */}
            <Grid container spacing={4}>
              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Utility Distribution by Agent Model
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={utilityChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="Positive Utility %" fill="#4CAF50" />
                      <Bar dataKey="Neutral Utility %" fill="#FFC107" />
                      <Bar dataKey="Negative Utility %" fill="#F44336" />
                    </BarChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Violation Percentages by Agent Model
                  </Typography>
                  <ResponsiveContainer width="100%" height={500}>
                    <BarChart data={violationChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      {violationTypes.slice(0, 5).map((type, index) => (
                        <Bar key={type} dataKey={formatViolationType(type)} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default ExperimentEthicalAnalysis; 