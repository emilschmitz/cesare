import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Tooltip,
  IconButton,
  Grid,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import { ContentCopy, Download, Assessment, Security, TrendingUp } from '@mui/icons-material';
import { experimentsAPI } from '../services/api';

const ExperimentViolationsSummary = ({ experimentName }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [markdownDialogOpen, setMarkdownDialogOpen] = useState(false);
  const [markdownContent, setMarkdownContent] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      if (!experimentName) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const result = await experimentsAPI.getExperimentViolationsSummary(experimentName);
        setData(result);
      } catch (err) {
        setError(err.message || 'Failed to fetch violations summary');
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
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getModelDisplayName = (modelName) => {
    if (!modelName || modelName === 'Unknown') return 'Unknown';
    
    // Handle string model names
    if (typeof modelName === 'string') {
      // If it contains a path separator, get the last part
      if (modelName.includes('/')) {
        return modelName.split('/').pop();
      }
      return modelName;
    }
    
    // Handle array or other types
    if (Array.isArray(modelName)) {
      return modelName.join(', ');
    }
    
    return String(modelName);
  };

  const generateCSV = () => {
    if (!data || !data.simulations) return '';

    const headers = [
      'Model',
      'Agent Temperature',
      'Environment Temperature',
      'Total Steps',
      'Total Instructions', 
      'Total Violations',
      'Ethical Risk Score',
      'Total Power Seeking',
      'Avg Power Seeking',
      'Total Disutility',
      'Avg Disutility',
      ...violationTypes.map(formatViolationType)
    ];

    const csvContent = [
      headers.join(','),
      ...data.simulations.map(sim => [
        `"${getModelDisplayName(sim.agent_model)}"`,
        sim.agent_temperature !== null && sim.agent_temperature !== undefined ? sim.agent_temperature : 'N/A',
        sim.environment_temperature !== null && sim.environment_temperature !== undefined ? sim.environment_temperature : 'N/A',
        sim.total_steps || 0,
        sim.total_instructions || 0,
        sim.total_violations,
        sim.ethical_risk_score || 0,
        sim.total_power_seeking || 0,
        sim.avg_power_seeking || 0,
        sim.total_disutility || 0,
        sim.avg_disutility || 0,
        ...violationTypes.map(type => sim[type] || 0)
      ].join(','))
    ].join('\n');

    return csvContent;
  };

  const downloadCSV = () => {
    const csvContent = generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${data.experiment_name}_ethical_analysis.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const generateMarkdown = () => {
    if (!data || !data.simulations) return '';

    let markdown = `# Ethical Analysis Summary: ${data.experiment_name}\n\n`;
    markdown += `**Total Simulations:** ${data.total_simulations}\n\n`;

    // Summary statistics
    const totalViolations = data.simulations.reduce((sum, sim) => sum + sim.total_violations, 0);
    const totalPowerSeeking = data.simulations.reduce((sum, sim) => sum + (sim.total_power_seeking || 0), 0);
    const totalDisutility = data.simulations.reduce((sum, sim) => sum + (sim.total_disutility || 0), 0);
    const avgRiskScore = data.simulations.reduce((sum, sim) => sum + (sim.ethical_risk_score || 0), 0) / data.simulations.length;

    markdown += `## Summary Statistics\n`;
    markdown += `- **Total Violations:** ${totalViolations}\n`;
    markdown += `- **Total Power-Seeking Behaviors:** ${totalPowerSeeking}\n`;
    markdown += `- **Total Disutility Events:** ${totalDisutility}\n`;
    markdown += `- **Average Ethical Risk Score:** ${avgRiskScore.toFixed(2)}\n\n`;

    // Create table header
    markdown += '| Model | Agent Temp | Env Temp | Steps | Instructions | Violations | Risk Score | Power Seeking | Disutility |';
    violationTypes.forEach(type => {
      markdown += ` ${formatViolationType(type)} |`;
    });
    markdown += '\n';

    // Create separator row
    markdown += '|-------|-----------|----------|-------|-------------|------------|------------|---------------|------------|';
    violationTypes.forEach(() => {
      markdown += '----------|';
    });
    markdown += '\n';

    // Add data rows
    data.simulations.forEach(sim => {
      const modelName = getModelDisplayName(sim.agent_model);
      const agentTemp = sim.agent_temperature !== null && sim.agent_temperature !== undefined ? sim.agent_temperature : 'N/A';
      const envTemp = sim.environment_temperature !== null && sim.environment_temperature !== undefined ? sim.environment_temperature : 'N/A';
      markdown += `| ${modelName} | ${agentTemp} | ${envTemp} | ${sim.total_steps || 0} | ${sim.total_instructions || 0} | ${sim.total_violations} | ${sim.ethical_risk_score || 0} | ${sim.total_power_seeking || 0} | ${sim.total_disutility || 0} |`;
      violationTypes.forEach(type => {
        markdown += ` ${sim[type]} |`;
      });
      markdown += '\n';
    });

    markdown += '\n---\n';
    markdown += `*Generated on ${new Date().toISOString().split('T')[0]}*\n`;

    return markdown;
  };

  const handleCopyMarkdown = () => {
    const markdown = generateMarkdown();
    setMarkdownContent(markdown);
    setMarkdownDialogOpen(true);
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(markdownContent);
      // You could add a snackbar notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getRiskScoreColor = (score) => {
    if (score === 0) return 'success';
    if (score <= 5) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data || !data.simulations || data.simulations.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No violations data found for experiment: {experimentName}
      </Alert>
    );
  }

  // Calculate summary statistics
  const totalViolations = data.simulations.reduce((sum, sim) => sum + sim.total_violations, 0);
  const totalPowerSeeking = data.simulations.reduce((sum, sim) => sum + (sim.total_power_seeking || 0), 0);
  const totalDisutility = data.simulations.reduce((sum, sim) => sum + (sim.total_disutility || 0), 0);
  const avgRiskScore = data.simulations.reduce((sum, sim) => sum + (sim.ethical_risk_score || 0), 0) / data.simulations.length;

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Security color="primary" />
          Ethical Analysis Summary
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Download as CSV">
            <IconButton onClick={downloadCSV} color="primary">
              <Download />
            </IconButton>
          </Tooltip>
          <Tooltip title="Copy as Markdown">
            <IconButton onClick={handleCopyMarkdown} color="primary">
              <ContentCopy />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
        Experiment: {data.experiment_name}
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment color="primary" />
                <Typography variant="h6">{data.total_simulations}</Typography>
              </Box>
              <Typography color="text.secondary">Total Simulations</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Security color="error" />
                <Typography variant="h6">{totalViolations}</Typography>
              </Box>
              <Typography color="text.secondary">Total Violations</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="warning" />
                <Typography variant="h6">{totalPowerSeeking}</Typography>
              </Box>
              <Typography color="text.secondary">Power-Seeking Behaviors</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment color="info" />
                <Typography variant="h6">{avgRiskScore.toFixed(1)}</Typography>
              </Box>
              <Typography color="text.secondary">Avg Risk Score</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Model</strong></TableCell>
              <TableCell align="center"><strong>Agent Temp</strong></TableCell>
              <TableCell align="center"><strong>Env Temp</strong></TableCell>
              <TableCell align="center"><strong>Steps</strong></TableCell>
              <TableCell align="center"><strong>Instructions</strong></TableCell>
              <TableCell align="center"><strong>Total Violations</strong></TableCell>
              <TableCell align="center"><strong>Risk Score</strong></TableCell>
              <TableCell align="center"><strong>Power Seeking</strong></TableCell>
              <TableCell align="center"><strong>Disutility</strong></TableCell>
              {violationTypes.map(type => (
                <TableCell key={type} align="center">
                  <strong>{formatViolationType(type)}</strong>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.simulations.map((sim, index) => {
              const modelName = getModelDisplayName(sim.agent_model);
              return (
                <TableRow key={sim.simulation_id} hover>
                  <TableCell>
                    <Tooltip title={sim.agent_model}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {modelName}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell align="center">
                    {sim.agent_temperature !== null && sim.agent_temperature !== undefined ? sim.agent_temperature : 'N/A'}
                  </TableCell>
                  <TableCell align="center">
                    {sim.environment_temperature !== null && sim.environment_temperature !== undefined ? sim.environment_temperature : 'N/A'}
                  </TableCell>
                  <TableCell align="center">{sim.total_steps || 0}</TableCell>
                  <TableCell align="center">{sim.total_instructions || 0}</TableCell>
                  <TableCell align="center">
                    <Chip 
                      label={sim.total_violations} 
                      color={sim.total_violations > 0 ? 'error' : 'success'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip 
                      label={sim.ethical_risk_score || 0} 
                      color={getRiskScoreColor(sim.ethical_risk_score || 0)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Box>
                      <Typography variant="body2">{sim.total_power_seeking || 0}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        (avg: {sim.avg_power_seeking || 0})
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Box>
                      <Typography variant="body2">{sim.total_disutility || 0}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        (avg: {sim.avg_disutility || 0})
                      </Typography>
                    </Box>
                  </TableCell>
                  {violationTypes.map(type => (
                    <TableCell key={type} align="center">
                      {sim[type] > 0 ? (
                        <Chip 
                          label={sim[type]} 
                          color="warning" 
                          size="small"
                          variant="outlined"
                        />
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          0
                        </Typography>
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Markdown Dialog */}
      <Dialog 
        open={markdownDialogOpen} 
        onClose={() => setMarkdownDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Markdown Table
          <IconButton
            onClick={copyToClipboard}
            sx={{ float: 'right' }}
            color="primary"
          >
            <ContentCopy />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            multiline
            fullWidth
            rows={15}
            value={markdownContent}
            variant="outlined"
            InputProps={{
              readOnly: true,
              sx: { fontFamily: 'monospace', fontSize: '0.875rem' }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMarkdownDialogOpen(false)}>Close</Button>
          <Button onClick={copyToClipboard} variant="contained">
            Copy to Clipboard
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExperimentViolationsSummary; 