"""
JMeter Plugin Support Module

Loads plugin configurations from extensions_config.yml and generates
plugin-specific JMX XML for JMeter tests.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class JMeterPluginSupport:
    """Support for JMeter plugins defined in extensions_config.yml"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize plugin support.
        
        Args:
            config_path: Path to extensions_config.yml (defaults to project root)
        """
        if config_path is None:
            # Default to project root
            config_path = Path(__file__).parent.parent / "extensions_config.yml"
        
        self.config_path = Path(config_path)
        self.plugins = {}
        self._load_config()
    
    def _load_config(self):
        """Load plugin configurations from extensions_config.yml"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            self.plugins = config.get('jmeter_plugins', {})
            self.plugin_paths = config.get('plugin_paths', {})
            self.auto_install = config.get('auto_install', {})
            
            logger.info(f"Loaded {len(self.plugins)} JMeter plugin configurations")
        except FileNotFoundError:
            logger.warning(f"Extensions config not found: {self.config_path}")
            self.plugins = {}
        except Exception as e:
            logger.error(f"Error loading extensions config: {e}")
            self.plugins = {}
    
    def is_plugin_available(self, plugin_name: str) -> bool:
        """Check if plugin is defined in config"""
        return plugin_name in self.plugins
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin configuration"""
        return self.plugins.get(plugin_name, {})
    
    def generate_plugin_sampler(
        self,
        plugin_name: str,
        sampler_name: str,
        plugin_config: Dict[str, Any]
    ) -> str:
        """
        Generate plugin-specific sampler XML.
        
        Args:
            plugin_name: Name of the plugin (e.g., 'grpc', 'mqtt')
            sampler_name: Name for this sampler instance
            plugin_config: Plugin-specific configuration from test YAML
            
        Returns:
            XML string for the plugin sampler
        """
        if not self.is_plugin_available(plugin_name):
            raise ValueError(f"Plugin '{plugin_name}' not found in extensions_config.yml")
        
        plugin_def = self.get_plugin_config(plugin_name)
        
        # Dispatch to plugin-specific generator
        if plugin_name == 'grpc':
            return self._generate_grpc_sampler(sampler_name, plugin_config, plugin_def)
        elif plugin_name == 'mqtt':
            return self._generate_mqtt_sampler(sampler_name, plugin_config, plugin_def)
        elif plugin_name == 'websocket':
            return self._generate_websocket_sampler(sampler_name, plugin_config, plugin_def)
        elif plugin_name == 'kafka':
            return self._generate_kafka_sampler(sampler_name, plugin_config, plugin_def)
        else:
            raise NotImplementedError(f"Plugin '{plugin_name}' generator not implemented yet")
    
    def _generate_grpc_sampler(
        self,
        sampler_name: str,
        config: Dict[str, Any],
        plugin_def: Dict[str, Any]
    ) -> str:
        """Generate gRPC sampler XML"""
        class_name = plugin_def['class_name']
        gui_class = plugin_def['gui_class']
        
        # Apply defaults from plugin definition
        props = plugin_def.get('properties', {})
        final_config = {}
        for prop_name, prop_def in props.items():
            if prop_name in config:
                final_config[prop_name] = config[prop_name]
            elif 'default' in prop_def:
                final_config[prop_name] = prop_def['default']
        
        xml = f'''
        <{class_name} guiclass="{gui_class}" testclass="{class_name}" testname="{sampler_name}" enabled="true">
          <stringProp name="host_port">{final_config.get('host_port', 'localhost:50051')}</stringProp>
          <stringProp name="proto_folder">{final_config.get('proto_folder', 'protos')}</stringProp>
          <stringProp name="lib_folder">{final_config.get('lib_folder', 'lib')}</stringProp>
          <stringProp name="full_method">{final_config.get('full_method', '')}</stringProp>
          <stringProp name="request_json">{final_config.get('request_json', '{}')}</stringProp>
          <stringProp name="metadata">{final_config.get('metadata', '{}')}</stringProp>
          <intProp name="deadline">{final_config.get('deadline', 10000)}</intProp>
          <boolProp name="tls">{str(final_config.get('tls', False)).lower()}</boolProp>
        </{class_name}>
        <hashTree/>
'''
        return xml
    
    def _generate_mqtt_sampler(
        self,
        sampler_name: str,
        config: Dict[str, Any],
        plugin_def: Dict[str, Any]
    ) -> str:
        """Generate MQTT sampler XML"""
        class_name = plugin_def['class_name']
        gui_class = plugin_def['gui_class']
        
        xml = f'''
        <{class_name} guiclass="{gui_class}" testclass="{class_name}" testname="{sampler_name}" enabled="true">
          <stringProp name="mqtt.server">{config.get('mqtt.server', 'tcp://localhost:1883')}</stringProp>
          <stringProp name="mqtt.client_id">{config.get('mqtt.client_id', 'jmeter_client')}</stringProp>
          <stringProp name="mqtt.topic">{config.get('mqtt.topic', 'test/topic')}</stringProp>
          <intProp name="mqtt.qos">{config.get('mqtt.qos', 0)}</intProp>
          <stringProp name="mqtt.message">{config.get('mqtt.message', '')}</stringProp>
          <boolProp name="mqtt.retained">{str(config.get('mqtt.retained', False)).lower()}</boolProp>
        </{class_name}>
        <hashTree/>
'''
        return xml
    
    def _generate_websocket_sampler(
        self,
        sampler_name: str,
        config: Dict[str, Any],
        plugin_def: Dict[str, Any]
    ) -> str:
        """Generate WebSocket sampler XML"""
        class_name = plugin_def['class_name']
        gui_class = plugin_def['gui_class']
        
        xml = f'''
        <{class_name} guiclass="{gui_class}" testclass="{class_name}" testname="{sampler_name}" enabled="true">
          <stringProp name="server_url">{config.get('server_url', 'ws://localhost:8080/ws')}</stringProp>
          <stringProp name="request_data">{config.get('request_data', '')}</stringProp>
          <stringProp name="response_pattern">{config.get('response_pattern', '')}</stringProp>
          <intProp name="connection_timeout">{config.get('connection_timeout', 20000)}</intProp>
          <intProp name="read_timeout">{config.get('read_timeout', 6000)}</intProp>
        </{class_name}>
        <hashTree/>
'''
        return xml
    
    def _generate_kafka_sampler(
        self,
        sampler_name: str,
        config: Dict[str, Any],
        plugin_def: Dict[str, Any]
    ) -> str:
        """Generate Kafka sampler XML"""
        class_name = plugin_def['class_name']
        gui_class = plugin_def['gui_class']
        
        xml = f'''
        <{class_name} guiclass="{gui_class}" testclass="{class_name}" testname="{sampler_name}" enabled="true">
          <stringProp name="bootstrap.servers">{config.get('bootstrap.servers', 'localhost:9092')}</stringProp>
          <stringProp name="topic">{config.get('topic', '')}</stringProp>
          <stringProp name="key">{config.get('key', '')}</stringProp>
          <stringProp name="message">{config.get('message', '')}</stringProp>
          <stringProp name="compression.type">{config.get('compression.type', 'none')}</stringProp>
        </{class_name}>
        <hashTree/>
'''
        return xml
    
    def validate_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate plugin configuration against schema.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.is_plugin_available(plugin_name):
            return False, [f"Plugin '{plugin_name}' not found in extensions_config.yml"]
        
        plugin_def = self.get_plugin_config(plugin_name)
        properties = plugin_def.get('properties', {})
        errors = []
        
        # Check required properties
        for prop_name, prop_def in properties.items():
            if prop_def.get('required', False) and prop_name not in config:
                errors.append(f"Required property '{prop_name}' missing for plugin '{plugin_name}'")
        
        return len(errors) == 0, errors
