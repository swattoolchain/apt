import {
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
    Chip,
} from '@mui/material';
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

const mockData = [
    { name: 'Test 1', duration: 1200, requests: 500, errors: 5 },
    { name: 'Test 2', duration: 980, requests: 450, errors: 2 },
    { name: 'Test 3', duration: 1500, requests: 600, errors: 8 },
    { name: 'Test 4', duration: 1100, requests: 520, errors: 3 },
    { name: 'Test 5', duration: 950, requests: 480, errors: 1 },
];

export default function Results() {
    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight={700}>
                Test Results
            </Typography>

            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Total Tests Run
                            </Typography>
                            <Typography variant="h3" fontWeight={700}>
                                24
                            </Typography>
                            <Chip label="+12% from last week" color="success" size="small" sx={{ mt: 1 }} />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Success Rate
                            </Typography>
                            <Typography variant="h3" fontWeight={700} color="success.main">
                                96.2%
                            </Typography>
                            <Chip label="+2.1% improvement" color="success" size="small" sx={{ mt: 1 }} />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Avg Response Time
                            </Typography>
                            <Typography variant="h3" fontWeight={700}>
                                1.1s
                            </Typography>
                            <Chip label="-150ms faster" color="success" size="small" sx={{ mt: 1 }} />
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight={600}>
                                Response Time Trend
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={mockData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="duration" stroke="#3b82f6" strokeWidth={2} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom fontWeight={600}>
                                Requests & Errors
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={mockData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="requests" fill="#3b82f6" />
                                    <Bar dataKey="errors" fill="#ef4444" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
