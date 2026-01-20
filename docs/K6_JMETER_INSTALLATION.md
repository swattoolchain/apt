# k6 and JMeter Installation & Execution Options

## Current Approach

k6 and JMeter are **optional external dependencies** - not bundled with the framework.

### Why Not Bundled?

1. **Large binaries** - k6 (~50MB), JMeter (~60MB)
2. **Platform-specific** - Different binaries for macOS, Linux, Windows
3. **Optional features** - Not everyone needs them
4. **Version flexibility** - Users can choose their versions

---

## Installation Options

### Option 1: Native Binaries (Recommended for Local Development)

#### k6
```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
# or
winget install k6 --source winget
```

#### JMeter
```bash
# macOS
brew install jmeter

# Linux
wget https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xzf apache-jmeter-5.6.3.tgz
export PATH=$PATH:$(pwd)/apache-jmeter-5.6.3/bin

# Windows
choco install jmeter
```

### Option 2: Docker (Recommended for CI/CD)

#### k6
```bash
# Pull image
docker pull grafana/k6:latest

# Run k6 test
docker run -v $(pwd):/scripts grafana/k6:latest run /scripts/load_test.js
```

#### JMeter
```bash
# Pull image
docker pull justb4/jmeter:latest

# Run JMeter test
docker run -v $(pwd):/tests justb4/jmeter:latest \
  -n -t /tests/load_test.jmx -l /tests/results.jtl
```

### Option 3: Framework Auto-Detection (Current Implementation)

The framework automatically detects if k6/JMeter are installed:

```python
# If k6 is installed, use it
# If not, show helpful error message with installation instructions
# Tests gracefully skip if tools not available
```

---

## How the Framework Uses Them

### Current Implementation

```python
# src/core/unified_runner.py

async def run_k6_test(self, ...):
    try:
        # Try to run k6 binary
        process = await asyncio.create_subprocess_exec(
            'k6', 'run', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # ...
    except FileNotFoundError:
        return {
            'status': 'error',
            'error': 'k6 not found. Install with: brew install k6'
        }
```

### With Docker Support (New)

```python
# Auto-detect: binary or Docker
if shutil.which('k6'):
    # Use native binary
    cmd = ['k6', 'run', script_path]
elif docker_available():
    # Use Docker
    cmd = ['docker', 'run', '-v', f'{cwd}:/scripts', 
           'grafana/k6:latest', 'run', '/scripts/test.js']
else:
    # Show error
    return {'error': 'k6 not available'}
```

---

## Recommended Approach by Environment

### Local Development
✅ **Native Binaries**
- Faster execution (no Docker overhead)
- Easier debugging
- Direct access to results

### CI/CD Pipelines
✅ **Docker**
- Consistent environment
- No installation needed
- Version pinning
- Parallel execution

### Production/Enterprise
✅ **Docker or Native** (depending on infrastructure)
- Docker for containerized environments
- Native for bare metal/VMs

---

## Configuration

### Specify Execution Method in YAML

```yaml
k6_tests:
  api_load:
    tool: "k6"
    execution:
      method: "docker"  # or "binary" or "auto"
      docker_image: "grafana/k6:0.48.0"  # Optional: pin version
    scenarios: [...]

jmeter_tests:
  load_test:
    tool: "jmeter"
    execution:
      method: "binary"  # or "docker" or "auto"
      docker_image: "justb4/jmeter:5.6.3"
    scenarios: [...]
```

### Environment Variable Override

```bash
# Force Docker execution
export PERF_K6_METHOD=docker
export PERF_JMETER_METHOD=docker

# Force binary execution
export PERF_K6_METHOD=binary
export PERF_JMETER_METHOD=binary

# Auto-detect (default)
export PERF_K6_METHOD=auto
```

---

## Docker Images

### Official Images

| Tool | Image | Size | Notes |
|------|-------|------|-------|
| k6 | `grafana/k6:latest` | ~50MB | Official Grafana image |
| k6 | `grafana/k6:0.48.0` | ~50MB | Pinned version |
| JMeter | `justb4/jmeter:latest` | ~400MB | Popular community image |
| JMeter | `justb4/jmeter:5.6.3` | ~400MB | Pinned version |

### Pre-pulling Images

```bash
# Pull images before running tests
docker pull grafana/k6:latest
docker pull justb4/jmeter:latest
```

---

## Framework Auto-Detection Logic

```
1. Check YAML config for execution.method
   ├─ If "docker" → Use Docker
   ├─ If "binary" → Use native binary
   └─ If "auto" or not specified → Auto-detect

2. Auto-detection priority:
   ├─ 1. Check for native binary (k6, jmeter)
   ├─ 2. Check for Docker
   └─ 3. Return error with installation instructions

3. Cache detection result for session
```

---

## Advantages of Current Approach

✅ **Flexible** - Users choose their installation method
✅ **Lightweight** - Framework stays small
✅ **Version Control** - Users control tool versions
✅ **CI/CD Friendly** - Works with Docker
✅ **Graceful Degradation** - Tests skip if tools unavailable

---

## Future Enhancements

### 1. Docker-First Mode
```bash
# Run framework in Docker with all tools included
docker run -v $(pwd):/tests neuron-perf-test:latest \
  pytest /tests/definitions/unified_test.yml
```

### 2. Tool Installer Script
```bash
# Auto-install k6 and JMeter
./scripts/install_tools.sh --method=docker
./scripts/install_tools.sh --method=binary
```

### 3. Cloud Execution
```bash
# Run k6 in k6 Cloud
k6 cloud script.js

# Run JMeter in BlazeMeter
```

---

## Summary

**Current State:**
- k6 and JMeter are **NOT bundled**
- Users install separately (binary or Docker)
- Framework auto-detects and uses them
- Graceful error if not available

**Recommended:**
- **Local Dev**: Install native binaries (`brew install k6 jmeter`)
- **CI/CD**: Use Docker images
- **Framework**: Auto-detects and uses what's available

**No bundling needed** - keeps framework lightweight and flexible! 🚀
