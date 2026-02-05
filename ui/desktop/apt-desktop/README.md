# APT Desktop - Tauri Application

Professional desktop application for the APT Performance Testing Framework.

## Features

✨ **Test Runner** - Select and run tests with live output
📝 **Test Editor** - Create tests with form-based UI (no YAML editing)
☁️ **Agent Manager** - Create, deploy, and monitor remote agents
📊 **Results Viewer** - Interactive charts and analytics
🎨 **Modern UI** - Dark theme with Material-UI components
🚀 **Native Performance** - Built with Tauri (Rust + React)

## Prerequisites

- **Node.js** 18+ and npm
- **Rust** 1.70+
- **Tauri CLI** (installed automatically)
- **APT Framework** (parent directory)

## Installation

```bash
cd apt-desktop

# Install dependencies
npm install

# Install Tauri CLI
npm install -g @tauri-apps/cli
```

## Development

```bash
# Run in development mode
npm run tauri:dev
```

This will:
1. Start Vite dev server (React frontend)
2. Launch Tauri window with hot-reload

## Building

```bash
# Build for production
npm run tauri:build
```

Output locations:
- **macOS**: `src-tauri/target/release/bundle/macos/APT Desktop.app`
- **Windows**: `src-tauri/target/release/bundle/msi/APT Desktop.msi`
- **Linux**: `src-tauri/target/release/bundle/deb/apt-desktop.deb`

## Project Structure

```
apt-desktop/
├── src/                    # React frontend
│   ├── components/         # Reusable components
│   │   └── Layout.tsx      # Main layout with sidebar
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Dashboard with stats
│   │   ├── TestRunner.tsx  # Test execution
│   │   ├── TestEditor.tsx  # Test creation
│   │   ├── AgentManager.tsx # Agent management
│   │   └── Results.tsx     # Results visualization
│   ├── App.tsx             # Main app component
│   └── main.tsx            # Entry point
├── src-tauri/              # Rust backend
│   ├── src/
│   │   └── main.rs         # Tauri commands
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri configuration
├── package.json            # Node dependencies
└── vite.config.ts          # Vite configuration
```

## Features Overview

### Dashboard
- Quick stats (total tests, pass/fail rate, active agents)
- Recent tests list
- Quick action buttons

### Test Runner
- Select test file from dropdown
- Run tests with one click
- Live output in terminal-style view
- Progress indicators

### Test Editor
- Form-based test creation
- Support for k6, JMeter, workflows
- Live YAML preview
- Save and run directly

### Agent Manager
- List all agents with status
- Create new agents
- Deploy to remote servers
- View logs and health status

### Results Viewer
- Interactive charts (response time, requests, errors)
- Trend analysis
- Success rate metrics
- Historical data

## Tauri Commands

The following Rust commands are available from the frontend:

- `run_pytest(test_file)` - Execute pytest
- `run_aptcli(args)` - Run aptcli commands
- `get_test_files(directory)` - List test files
- `read_yaml_file(file_path)` - Read YAML content
- `write_yaml_file(file_path, content)` - Write YAML file

## Usage

### Running a Test

1. Open **Test Runner** from sidebar
2. Select test file from dropdown
3. Click **Run Test**
4. View live output

### Creating a Test

1. Open **Test Editor** from sidebar
2. Fill in test details (name, URL, VUs, duration)
3. Preview generated YAML
4. Click **Save Test** or **Save & Run**

### Managing Agents

1. Open **Agents** from sidebar
2. Click **Create Agent**
3. Enter agent name and type
4. Deploy to remote server (manual or via aptcli)
5. Monitor status

## Keyboard Shortcuts

- `Cmd/Ctrl + R` - Refresh test list
- `Cmd/Ctrl + N` - New test
- `Cmd/Ctrl + S` - Save test

## Troubleshooting

### Build Errors

```bash
# Clean build
rm -rf src-tauri/target
npm run tauri:build
```

### Development Server Issues

```bash
# Kill existing processes
pkill -f vite
pkill -f tauri

# Restart
npm run tauri:dev
```

### Permission Issues (macOS)

```bash
# Allow app to run
xattr -cr "src-tauri/target/release/bundle/macos/APT Desktop.app"
```

## Technologies

- **Frontend**: React 18, TypeScript, Material-UI, Recharts
- **Backend**: Tauri (Rust), FastAPI integration
- **Build**: Vite, Tauri CLI
- **State**: Zustand (lightweight state management)
- **Routing**: React Router v6

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test with `npm run tauri:dev`
5. Build with `npm run tauri:build`
6. Submit pull request

## License

MIT License - see parent project LICENSE

## Support

- **Documentation**: See parent project docs/
- **Issues**: Report on GitHub
- **Discussions**: Ask questions in GitHub Discussions

---

**Built with ❤️ using Tauri**
