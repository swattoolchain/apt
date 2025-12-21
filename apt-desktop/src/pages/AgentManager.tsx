import { useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
} from '@mui/material';
import {
    Add,
    Delete,
    Refresh,
    CloudUpload,
    Visibility,
} from '@mui/icons-material';
import { invoke } from '@tauri-apps/api/tauri';

interface Agent {
    id: string;
    name: string;
    type: string;
    status: 'healthy' | 'unhealthy' | 'unknown';
    endpoint?: string;
}

export default function AgentManager() {
    const [agents, setAgents] = useState<Agent[]>([
        { id: '1', name: 'us-east-1', type: 'docker', status: 'healthy', endpoint: 'http://server1.com:9090' },
        { id: '2', name: 'eu-west-1', type: 'systemd', status: 'unknown', endpoint: 'http://server2.com:9090' },
    ]);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [newAgentName, setNewAgentName] = useState('');
    const [newAgentType, setNewAgentType] = useState('docker');

    const createAgent = async () => {
        try {
            await invoke('run_aptcli', {
                args: ['agent', 'create', '--name', newAgentName, '--type', newAgentType, '--mode', 'emit'],
            });

            setAgents([
                ...agents,
                {
                    id: Date.now().toString(),
                    name: newAgentName,
                    type: newAgentType,
                    status: 'unknown',
                },
            ]);

            setCreateDialogOpen(false);
            setNewAgentName('');
        } catch (error) {
            console.error('Failed to create agent:', error);
        }
    };

    const deleteAgent = (id: string) => {
        setAgents(agents.filter((agent) => agent.id !== id));
    };

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" fontWeight={700}>
                    Agent Manager
                </Typography>
                <Box display="flex" gap={2}>
                    <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={() => {
                            // Refresh agents
                        }}
                    >
                        Refresh
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<Add />}
                        onClick={() => setCreateDialogOpen(true)}
                    >
                        Create Agent
                    </Button>
                </Box>
            </Box>

            <Card>
                <CardContent>
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Endpoint</TableCell>
                                    <TableCell align="right">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {agents.map((agent) => (
                                    <TableRow key={agent.id}>
                                        <TableCell>{agent.name}</TableCell>
                                        <TableCell>
                                            <Chip label={agent.type} size="small" />
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={agent.status}
                                                size="small"
                                                color={
                                                    agent.status === 'healthy'
                                                        ? 'success'
                                                        : agent.status === 'unhealthy'
                                                            ? 'error'
                                                            : 'default'
                                                }
                                            />
                                        </TableCell>
                                        <TableCell>{agent.endpoint || '-'}</TableCell>
                                        <TableCell align="right">
                                            <IconButton size="small" title="View Logs">
                                                <Visibility />
                                            </IconButton>
                                            <IconButton size="small" title="Deploy">
                                                <CloudUpload />
                                            </IconButton>
                                            <IconButton
                                                size="small"
                                                color="error"
                                                title="Delete"
                                                onClick={() => deleteAgent(agent.id)}
                                            >
                                                <Delete />
                                            </IconButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
                <DialogTitle>Create New Agent</DialogTitle>
                <DialogContent>
                    <Box display="flex" flexDirection="column" gap={2} pt={1}>
                        <TextField
                            label="Agent Name"
                            value={newAgentName}
                            onChange={(e) => setNewAgentName(e.target.value)}
                            fullWidth
                        />
                        <TextField
                            select
                            label="Deployment Type"
                            value={newAgentType}
                            onChange={(e) => setNewAgentType(e.target.value)}
                            fullWidth
                            SelectProps={{ native: true }}
                        >
                            <option value="docker">Docker</option>
                            <option value="cron">Cron</option>
                            <option value="systemd">Systemd</option>
                            <option value="shell">Shell</option>
                        </TextField>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={createAgent}>
                        Create
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
