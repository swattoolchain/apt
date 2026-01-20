import { useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    TextField,
    Button,
    Grid,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
} from '@mui/material';
import { Save, PlayArrow } from '@mui/icons-material';
import { invoke } from '@tauri-apps/api/tauri';

export default function TestEditor() {
    const [testName, setTestName] = useState('');
    const [testType, setTestType] = useState('k6');
    const [url, setUrl] = useState('');
    const [vus, setVus] = useState('10');
    const [duration, setDuration] = useState('30s');
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');

    const generateYAML = () => {
        const yaml = `test_info:
  test_suite_name: "${testName}"
  description: "Generated test"
  version: "1.0"

k6_tests:
  ${testName.toLowerCase().replace(/\s+/g, '_')}:
    scenarios:
      - name: "Test Scenario"
        url: "${url}"
        method: "GET"
    
    options:
      vus: ${vus}
      duration: "${duration}"
      thresholds:
        http_req_duration: ["p(95)<500"]

reporting:
  output_dir: "performance_results/${testName.toLowerCase().replace(/\s+/g, '_')}"
  include:
    - k6
`;
        return yaml;
    };

    const saveTest = async () => {
        if (!testName || !url) {
            setError('Please fill in all required fields');
            return;
        }

        try {
            const yaml = generateYAML();
            const fileName = `./examples/${testName.toLowerCase().replace(/\s+/g, '_')}.yml`;

            await invoke('write_yaml_file', {
                filePath: fileName,
                content: yaml,
            });

            setSuccess(`Test saved successfully: ${fileName}`);
            setError('');
        } catch (err) {
            setError('Failed to save test: ' + err);
            setSuccess('');
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight={700}>
                Test Editor
            </Typography>

            <Card>
                <CardContent>
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Test Name"
                                value={testName}
                                onChange={(e) => setTestName(e.target.value)}
                                required
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <FormControl fullWidth>
                                <InputLabel>Test Type</InputLabel>
                                <Select
                                    value={testType}
                                    label="Test Type"
                                    onChange={(e) => setTestType(e.target.value)}
                                >
                                    <MenuItem value="k6">k6 (API Load Test)</MenuItem>
                                    <MenuItem value="jmeter">JMeter (Protocol Test)</MenuItem>
                                    <MenuItem value="workflow">Custom Workflow</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Target URL"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                                placeholder="https://api.example.com/endpoint"
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Virtual Users (VUs)"
                                type="number"
                                value={vus}
                                onChange={(e) => setVus(e.target.value)}
                            />
                        </Grid>

                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Duration"
                                value={duration}
                                onChange={(e) => setDuration(e.target.value)}
                                placeholder="30s, 1m, 5m"
                            />
                        </Grid>

                        <Grid item xs={12}>
                            <Box display="flex" gap={2}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    startIcon={<Save />}
                                    onClick={saveTest}
                                >
                                    Save Test
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="large"
                                    startIcon={<PlayArrow />}
                                    onClick={() => {
                                        saveTest();
                                        // Navigate to test runner
                                        setTimeout(() => {
                                            window.location.href = '/test-runner';
                                        }, 1000);
                                    }}
                                >
                                    Save & Run
                                </Button>
                            </Box>
                        </Grid>

                        {success && (
                            <Grid item xs={12}>
                                <Alert severity="success">{success}</Alert>
                            </Grid>
                        )}

                        {error && (
                            <Grid item xs={12}>
                                <Alert severity="error">{error}</Alert>
                            </Grid>
                        )}
                    </Grid>
                </CardContent>
            </Card>

            <Card sx={{ mt: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                        Generated YAML Preview
                    </Typography>
                    <Box
                        component="pre"
                        sx={{
                            p: 2,
                            bgcolor: 'background.default',
                            borderRadius: 1,
                            overflow: 'auto',
                            fontSize: '0.875rem',
                        }}
                    >
                        {generateYAML()}
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
}
