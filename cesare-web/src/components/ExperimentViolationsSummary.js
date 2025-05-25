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
  IconButton
} from '@mui/material';
import { ContentCopy } from '@mui/icons-material';
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

  const generateMarkdown = () => {
    if (!data || !data.simulations) return '';

    let markdown = `# Violations Summary: ${data.experiment_name}\n\n`;
    markdown += `**Total Simulations:** ${data.total_simulations}\n\n`;

    // Create table header
    markdown += '| Model | Total Steps | Total Instructions | Total Violations |';
    violationTypes.forEach(type => {
      markdown += ` ${formatViolationType(type)} |`;
    });
    markdown += '\n';

    // Create separator row
    markdown += '|-------|-------------|-------------------|------------------|';
    violationTypes.forEach(() => {
      markdown += '----------|';
    });
    markdown += '\n';

    // Add data rows
    data.simulations.forEach(sim => {
      const modelName = sim.agent_model.split('/').pop() || sim.agent_model;
      markdown += `| ${modelName} | ${sim.total_steps || 0} | ${sim.total_instructions || 0} | ${sim.total_violations} |`;
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

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          Violations Summary: {data.experiment_name}
        </Typography>
        <Box>
          <Tooltip title="Copy as Markdown">
            <IconButton onClick={handleCopyMarkdown} color="primary">
              <ContentCopy />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Total Simulations: {data.total_simulations}
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Model</strong></TableCell>
              <TableCell align="center"><strong>Steps</strong></TableCell>
              <TableCell align="center"><strong>Instructions</strong></TableCell>
              <TableCell align="center"><strong>Total Violations</strong></TableCell>
              {violationTypes.map(type => (
                <TableCell key={type} align="center">
                  <strong>{formatViolationType(type)}</strong>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.simulations.map((sim, index) => {
              const modelName = sim.agent_model.split('/').pop() || sim.agent_model;
              return (
                <TableRow key={sim.simulation_id} hover>
                  <TableCell>
                    <Tooltip title={sim.agent_model}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {modelName}
                      </Typography>
                    </Tooltip>
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