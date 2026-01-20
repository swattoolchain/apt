# JMeter Plugins Configuration Guide

## Overview

APT supports JMeter plugins for advanced testing scenarios like gRPC, MQTT, WebSocket, and more. This guide explains how to install, configure, and use JMeter plugins in your performance tests.

## Installing JMeter Plugins

### Method 1: JMeter Plugins Manager (Recommended)

1. **Install Plugins Manager:**
```bash
cd /opt/homebrew/Cellar/jmeter/5.6.3/libexec/lib/ext/
wget https://jmeter-plugins.org/get/ -O jmeter-plugins-manager.jar
```

2. **Install Specific Plugins via Command Line:**
```bash
# Install gRPC plugin
jmeter -Jjmeterengine.nongui.port=0 -Jjmeterengine.nongui.maxport=0 \
  -Jplugin-install=jpgc-grpc

# Install MQTT plugin
jmeter -Jplugin-install=jpgc-mqtt

# Install WebSocket plugin
jmeter -Jplugin-install=jpgc-websocket
```

### Method 2: Manual Installation

Download plugin JARs and place them in:
```
/opt/homebrew/Cellar/jmeter/5.6.3/libexec/lib/ext/
```

## Common JMeter Plugins

### 1. gRPC Plugin
- **Plugin Name:** `jpgc-grpc`
- **Use Case:** Testing gRPC services
- **Download:** https://github.com/zalopay-oss/jmeter-grpc-plugin

### 2. MQTT Plugin
- **Plugin Name:** `jpgc-mqtt`
- **Use Case:** IoT and messaging protocols
- **Download:** https://github.com/emqx/mqtt-jmeter

### 3. WebSocket Plugin
- **Plugin Name:** `jpgc-websocket`
- **Use Case:** Real-time communication testing
- **Download:** https://bitbucket.org/pjtr/jmeter-websocket-samplers

### 4. Kafka Plugin
- **Plugin Name:** `jpgc-kafka`
- **Use Case:** Event streaming testing

## Configuring Plugins in APT

### Option 1: Custom JMX File

For complex plugin configurations, create a custom JMX file and reference it:

```yaml
jmeter_tests:
  grpc_test:
    tool: "jmeter"
    jmx_file: "tests/jmeter/grpc_test.jmx"  # Custom JMX with plugin config
    thread_group_config:
      num_threads: 10
      duration: 60
```

### Option 2: Plugin-Specific Configuration (Future Enhancement)

APT can be extended to support plugin-specific YAML configuration:

```yaml
jmeter_tests:
  grpc_load_test:
    tool: "jmeter"
    plugin: "grpc"
    plugin_config:
      proto_file: "protos/service.proto"
      host: "localhost:50051"
      method: "MyService/GetUser"
      request_data: |
        {
          "user_id": "123"
        }
    thread_group_config:
      num_threads: 20
      duration: 60
```

## Example: gRPC Testing with JMeter

### Step 1: Install gRPC Plugin

```bash
# Download gRPC plugin
cd /opt/homebrew/Cellar/jmeter/5.6.3/libexec/lib/ext/
wget https://github.com/zalopay-oss/jmeter-grpc-plugin/releases/download/v1.2.4/jmeter-grpc-request-1.2.4.jar
```

### Step 2: Create JMX File with gRPC Sampler

Create `tests/jmeter/grpc_example.jmx`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="gRPC Test">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <stringProp name="ThreadGroup.num_threads">10</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <longProp name="ThreadGroup.duration">60</longProp>
      </ThreadGroup>
      <hashTree>
        <!-- gRPC Request Sampler -->
        <vn.zalopay.benchmark.GRPCClientSampler guiclass="vn.zalopay.benchmark.gui.GRPCClientSamplerGui" 
                                                 testclass="vn.zalopay.benchmark.GRPCClientSampler" 
                                                 testname="gRPC Request">
          <stringProp name="host_port">localhost:50051</stringProp>
          <stringProp name="proto_folder">protos</stringProp>
          <stringProp name="lib_folder">lib</stringProp>
          <stringProp name="full_method">MyService/GetUser</stringProp>
          <stringProp name="request_json">{"user_id": "123"}</stringProp>
        </vn.zalopay.benchmark.GRPCClientSampler>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### Step 3: Reference in YAML Test

```yaml
test_info:
  test_suite_name: "gRPC Load Test"
  test_suite_type: "unified"

jmeter_tests:
  grpc_service_test:
    tool: "jmeter"
    jmx_file: "tests/jmeter/grpc_example.jmx"
    thread_group_config:
      num_threads: 20
      duration: 120
```

## Plugin Configuration Best Practices

### 1. Version Compatibility
- Ensure plugin versions are compatible with your JMeter version (5.6.3)
- Check plugin documentation for compatibility matrix

### 2. Dependencies
- Some plugins require additional JAR dependencies
- Place all dependencies in `/opt/homebrew/Cellar/jmeter/5.6.3/libexec/lib/ext/`

### 3. Testing Plugin Installation
```bash
# Verify plugin is loaded
jmeter -v
jmeter -?
```

### 4. Custom Samplers
For plugins with custom samplers, you must use JMX files as APT's YAML generator doesn't support custom sampler types yet.

## Environment Variables for Plugins

Set plugin-specific environment variables:

```yaml
jmeter_tests:
  plugin_test:
    tool: "jmeter"
    jmx_file: "tests/jmeter/custom.jmx"
    environment:
      GRPC_HOST: "localhost:50051"
      MQTT_BROKER: "tcp://localhost:1883"
    thread_group_config:
      num_threads: 10
      duration: 60
```

## Extending APT for Plugin Support

To add native plugin support to APT, you can extend the `JMeterIntegration` class:

```python
# src/core/jmeter_plugins.py
class JMeterPluginSupport:
    @staticmethod
    def generate_grpc_sampler(config):
        """Generate gRPC sampler XML"""
        return f'''
        <vn.zalopay.benchmark.GRPCClientSampler>
          <stringProp name="host_port">{config['host']}</stringProp>
          <stringProp name="full_method">{config['method']}</stringProp>
          <stringProp name="request_json">{config['request']}</stringProp>
        </vn.zalopay.benchmark.GRPCClientSampler>
        '''
```

## Troubleshooting

### Plugin Not Loading
1. Check plugin JAR is in correct directory
2. Verify JMeter version compatibility
3. Check for dependency conflicts
4. Review JMeter logs: `/opt/homebrew/Cellar/jmeter/5.6.3/libexec/bin/jmeter.log`

### Custom Sampler Not Found
- Ensure plugin class name matches exactly in JMX file
- Verify plugin JAR contains the sampler class

## Next Steps

1. **Install Required Plugins:** Use JMeter Plugins Manager
2. **Create JMX Templates:** Build reusable JMX files for common scenarios
3. **Extend APT:** Add native YAML support for your most-used plugins
4. **Document Custom Configs:** Maintain plugin configuration documentation

## References

- [JMeter Plugins](https://jmeter-plugins.org/)
- [gRPC Plugin](https://github.com/zalopay-oss/jmeter-grpc-plugin)
- [MQTT Plugin](https://github.com/emqx/mqtt-jmeter)
- [WebSocket Plugin](https://bitbucket.org/pjtr/jmeter-websocket-samplers)
