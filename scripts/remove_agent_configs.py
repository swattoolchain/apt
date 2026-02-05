#!/usr/bin/env python3
"""
Script to remove agent configurations from all test YAML files.
All agents are now loaded from config/agents.yml (global agent pool).
"""

import yaml
import re
from pathlib import Path

def remove_agents_section(file_path):
    """Remove the agents section from a YAML file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if file has agents section
    if 'agents:' not in content:
        print(f"  ⏭️  Skipping {file_path.name} (no agents section)")
        return False
    
    # Load YAML to preserve structure
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        print(f"  ❌ Error loading {file_path.name}: {e}")
        return False
    
    # Check if agents section exists
    if 'agents' not in data:
        print(f"  ⏭️  Skipping {file_path.name} (no agents in data)")
        return False
    
    # Remove agents section
    del data['agents']
    
    # Update version if exists
    if 'test_info' in data and 'version' in data['test_info']:
        current_version = data['test_info']['version']
        # Increment version
        try:
            version_num = float(current_version)
            data['test_info']['version'] = str(version_num + 1.0)
        except:
            data['test_info']['version'] = "4.0"
    
    # Write back with comment
    with open(file_path, 'w') as f:
        # Write header comments (preserve existing)
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                f.write(line + '\n')
            else:
                break
        
        # Add global agent pool comment if not already present
        if 'Global Agent Pool' not in content:
            f.write('# ✅ Agents loaded from config/agents.yml (Global Agent Pool)\n')
        
        f.write('\n')
        
        # Write YAML without agents section
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"  ✅ Removed agents from {file_path.name}")
    return True

def main():
    examples_dir = Path('examples')
    
    # Files to process
    files_to_process = [
        '03_multi_region_test.yml',
        '04_production_monitoring.yml',
        '06_external_agent_code.yml',
        '08_advanced_agents.yml',
        '09_async_distributed_browsers.yml',
        '10_weighted_load_distribution.yml',
        '12_parallel_execution.yml',
        'agent_test.yml',
    ]
    
    print("🔧 Removing agent configurations from test files...")
    print("=" * 60)
    
    modified_count = 0
    for filename in files_to_process:
        file_path = examples_dir / filename
        if file_path.exists():
            if remove_agents_section(file_path):
                modified_count += 1
        else:
            print(f"  ⚠️  File not found: {filename}")
    
    print("=" * 60)
    print(f"✅ Modified {modified_count} files")
    print("📝 All agents now loaded from config/agents.yml")

if __name__ == '__main__':
    main()
