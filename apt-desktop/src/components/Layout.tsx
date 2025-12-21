import { ReactNode, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Box,
    Drawer,
    AppBar,
    Toolbar,
    List,
    Typography,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    IconButton,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    PlayArrow,
    Edit,
    Cloud,
    Assessment,
    Menu as MenuIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

interface LayoutProps {
    children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();

    const menuItems = [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
        { text: 'Test Runner', icon: <PlayArrow />, path: '/test-runner' },
        { text: 'Test Editor', icon: <Edit />, path: '/test-editor' },
        { text: 'Agents', icon: <Cloud />, path: '/agents' },
        { text: 'Results', icon: <Assessment />, path: '/results' },
    ];

    const drawer = (
        <Box>
            <Toolbar>
                <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
                    APT Desktop
                </Typography>
            </Toolbar>
            <List>
                {menuItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            selected={location.pathname === item.path}
                            onClick={() => navigate(item.path)}
                            sx={{
                                '&.Mui-selected': {
                                    backgroundColor: 'primary.main',
                                    '&:hover': {
                                        backgroundColor: 'primary.dark',
                                    },
                                },
                            }}
                        >
                            <ListItemIcon sx={{ color: location.pathname === item.path ? 'white' : 'inherit' }}>
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
            <AppBar
                position="fixed"
                sx={{
                    width: { sm: `calc(100% - ${drawerWidth}px)` },
                    ml: { sm: `${drawerWidth}px` },
                    display: { sm: 'none' },
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        edge="start"
                        onClick={() => setMobileOpen(!mobileOpen)}
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div">
                        APT Desktop
                    </Typography>
                </Toolbar>
            </AppBar>
            <Box
                component="nav"
                sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
            >
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={() => setMobileOpen(false)}
                    ModalProps={{ keepMounted: true }}
                    sx={{
                        display: { xs: 'block', sm: 'none' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                >
                    {drawer}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', sm: 'block' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: { sm: `calc(100% - ${drawerWidth}px)` },
                    overflow: 'auto',
                }}
            >
                <Toolbar sx={{ display: { sm: 'none' } }} />
                {children}
            </Box>
        </Box>
    );
}
