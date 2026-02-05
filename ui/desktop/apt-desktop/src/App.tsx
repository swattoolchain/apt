import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TestRunner from './pages/TestRunner';
import TestEditor from './pages/TestEditor';
import AgentManager from './pages/AgentManager';
import Results from './pages/Results';

const darkTheme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#3b82f6',
        },
        secondary: {
            main: '#8b5cf6',
        },
        background: {
            default: '#0f172a',
            paper: '#1e293b',
        },
    },
    typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    borderRadius: 8,
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                },
            },
        },
    },
});

function App() {
    return (
        <ThemeProvider theme={darkTheme}>
            <CssBaseline />
            <BrowserRouter>
                <Layout>
                    <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/test-runner" element={<TestRunner />} />
                        <Route path="/test-editor" element={<TestEditor />} />
                        <Route path="/agents" element={<AgentManager />} />
                        <Route path="/results" element={<Results />} />
                    </Routes>
                </Layout>
            </BrowserRouter>
        </ThemeProvider>
    );
}

export default App;
