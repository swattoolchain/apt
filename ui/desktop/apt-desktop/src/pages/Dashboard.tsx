import { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Button,
    Chip,
    List,
    ListItem,
    ListItemText,
} from '@mui/material';
import {
    PlayArrow,
    CheckCircle,
    Error,
    Cloud,
    Assessment,
} from '@mui/icons-material';
import { invoke } from '@tauri-apps/api/tauri';

interface TestFile {
    name: string;
    path: string;
}

interface AgentStatus {
    name: string;
    status: 'healthy' | 'unhealthy' | 'unknown';
}

export default function Dashboard() {
    const [recentTests, setRecentTests] = useState<TestFile[]>([]);
    const [agents, setAgents] = useState<AgentStatus[]>([]);
    const [stats, setStats] = useState({
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        activeAgents: 0,
    });

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            // Load test files
            const files = await invoke<string[]>('get_test_files', {
                directory: './examples',
            });

            setRecentTests(
                files.slice(0, 5).map((path) => ({
                    name: path.split('/').pop() || '',
                    path,
                }))
            );

            // Mock stats for now
            setStats({
                totalTests: files.length,
                passedTests: Math.floor(files.length * 0.8),
                failedTests: Math.floor(files.length * 0.2),
                activeAgents: 2,
            });
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight={700}>
                Dashboard
            </Typography>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Total Tests
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700}>
                                        {stats.totalTests}
                                    </Typography>
                                </Box>
                                <Assessment sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Passed
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700} color="success.main">
                                        {stats.passedTests}
                                    </Typography>
                                </Box>
                                <CheckCircle sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Failed
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700} color="error.main">
                                        {stats.failedTests}
                                    </Typography>
                                </Box>
                                <Error sx={{ fontSize: 48, color: 'error.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                                <Box>
                                    <Typography color="text.secondary" gutterBottom>
                                        Active Agents
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700}>
                                        {stats.activeAgents}
                                    </Typography>
                                </Box>
                                <Cloud sx={{ fontSize: 48, color: 'secondary.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Recent Tests */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight={600}>
                                Recent Tests
                            </Typography>
                            <List>
                                {recentTests.map((test, index) => (
                                    <ListItem
                                        key={index}
                                        secondaryAction={
                                            <Button
                                                variant="contained"
                                                size="small"
                                                startIcon={<PlayArrow />}
                                                onClick={() => {
                                                    // Navigate to test runner with this test
                                                    window.location.href = `/test-runner?file=${encodeURIComponent(test.path)}`;
                                                }}
                                            >
                                                Run
                                            </Button>
                                        }
                                    >
                                        <ListItemText
                                            primary={test.name}
                                            secondary={test.path}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight={600}>
                                Quick Actions
                            </Typography>
                            <Box display="flex" flexDirection="column" gap={2} mt={2}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    startIcon={<PlayArrow />}
                                    fullWidth
                                    onClick={() => (window.location.href = '/test-runner')}
                                >
                                    Run Test
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="large"
                                    fullWidth
                                    onClick={() => (window.location.href = '/test-editor')}
                                >
                                    Create New Test
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="large"
                                    fullWidth
                                    onClick={() => (window.location.href = '/agents')}
                                >
                                    Manage Agents
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="large"
                                    fullWidth
                                    onClick={() => (window.location.href = '/results')}
                                >
                                    View Results
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
