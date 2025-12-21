import { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    CircularProgress,
    Paper,
    LinearProgress,
} from '@mui/material';
import { PlayArrow, Stop, Refresh } from '@mui/icons-material';
import { invoke } from '@tauri-apps/api/tauri';

export default function TestRunner() {
    const [testFiles, setTestFiles] = useState<string[]>([]);
    const [selectedTest, setSelectedTest] = useState('');
    const [running, setRunning] = useState(false);
    const [output, setOutput] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        loadTestFiles();
    }, []);

    const loadTestFiles = async () => {
        try {
            const files = await invoke<string[]>('get_test_files', {
                directory: './examples',
            });
            setTestFiles(files);
            if (files.length > 0) {
                setSelectedTest(files[0]);
            }
        } catch (err) {
            setError('Failed to load test files: ' + err);
        }
    };

    const runTest = async () => {
        if (!selectedTest) return;

        setRunning(true);
        setOutput('');
        setError('');

        try {
            const result = await invoke<string>('run_pytest', {
                testFile: selectedTest,
            });
            setOutput(result);
        } catch (err) {
            setError('Test execution failed: ' + err);
        } finally {
            setRunning(false);
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight={700}>
                Test Runner
            </Typography>

            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Box display="flex" gap={2} alignItems="center">
                        <FormControl fullWidth>
                            <InputLabel>Select Test File</InputLabel>
                            <Select
                                value={selectedTest}
                                label="Select Test File"
                                onChange={(e) => setSelectedTest(e.target.value)}
                                disabled={running}
                            >
                                {testFiles.map((file) => (
                                    <MenuItem key={file} value={file}>
                                        {file.split('/').pop()}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        <Button
                            variant="contained"
                            size="large"
                            startIcon={running ? <Stop /> : <PlayArrow />}
                            onClick={runTest}
                            disabled={!selectedTest || running}
                            sx={{ minWidth: 120 }}
                        >
                            {running ? 'Running...' : 'Run Test'}
                        </Button>

                        <Button
                            variant="outlined"
                            size="large"
                            startIcon={<Refresh />}
                            onClick={loadTestFiles}
                            disabled={running}
                        >
                            Refresh
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {running && (
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Box display="flex" alignItems="center" gap={2}>
                            <CircularProgress size={24} />
                            <Typography>Test execution in progress...</Typography>
                        </Box>
                        <LinearProgress sx={{ mt: 2 }} />
                    </CardContent>
                </Card>
            )}

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {output && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom fontWeight={600}>
                            Test Output
                        </Typography>
                        <Paper
                            sx={{
                                p: 2,
                                bgcolor: '#000',
                                color: '#0f0',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                                maxHeight: '500px',
                                overflow: 'auto',
                                whiteSpace: 'pre-wrap',
                            }}
                        >
                            {output}
                        </Paper>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}
