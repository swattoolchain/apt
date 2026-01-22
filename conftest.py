"""
Pytest configuration for APT framework.
Automatically loads the YAML test plugin.
"""

# Import the plugin to register it
pytest_plugins = ["src.test_scripts.pytest_perf_plugin"]
