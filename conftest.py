"""
Pytest configuration for APT framework.
Automatically loads the YAML test plugin.
"""

# Import the plugin to register it
pytest_plugins = ["tests.pytest_perf_plugin"]
