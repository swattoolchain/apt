#!/usr/bin/env python3
"""
aptcli - APT Framework Command Line Interface

Main entry point for the APT CLI tool.
Provides commands for agent management, testbed setup, and test execution.

Usage:
    aptcli agent create --name <name> --type <type> --mode <mode>
    aptcli agent deploy --name <name> --target <ssh-target>
    aptcli agent status [--name <name>]
    aptcli testbed setup --config <file>
    aptcli run <test-file>
"""

import click
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@click.group()
@click.version_option(version='1.0.0', prog_name='aptcli')
def cli():
    """APT Framework - Allied Performance Testing CLI"""
    pass


@cli.group()
def agent():
    """Manage remote agents"""
    pass


@agent.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--type', 'deploy_type', type=click.Choice(['docker', 'cron', 'systemd', 'shell']), required=True, help='Deployment type')
@click.option('--mode', type=click.Choice(['emit', 'serve']), required=True, help='Agent mode')
@click.option('--emit-target', help='InfluxDB URL for emit mode')
@click.option('--auth-token', help='Authentication token (generated if not provided)')
@click.option('--schedule', help='Cron schedule (for cron type)', default='*/5 * * * *')
def create(name, deploy_type, mode, emit_target, auth_token, schedule):
    """Create a new agent package"""
    try:
        from performance.agents import AgentProvisioner, DeploymentMethod
        import secrets
        
        # Generate auth token if not provided
        if not auth_token:
            auth_token = secrets.token_urlsafe(32)
            click.echo(f"🔑 Generated auth token: {auth_token}")
            click.echo("   Save this token securely!")
        
        # Map string to enum
        method_map = {
            'docker': DeploymentMethod.DOCKER,
            'cron': DeploymentMethod.CRON,
            'systemd': DeploymentMethod.SYSTEMD,
            'shell': DeploymentMethod.SHELL
        }
        
        # Create config
        config = {
            'mode': mode,
            'emit_target': emit_target or '',
            'auth_token': auth_token,
            'schedule': schedule
        }
        
        # Create agent package
        provisioner = AgentProvisioner()
        package_dir = provisioner.create_agent(name, method_map[deploy_type], config)
        
        click.echo(f"\n✅ Agent package created: {package_dir}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Review package: cd {package_dir}")
        click.echo(f"  2. Deploy: aptcli agent deploy --name {name} --target user@host")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--target', required=True, help='SSH target (user@host)')
@click.option('--ssh-key', help='Path to SSH private key')
@click.option('--type', 'deploy_type', type=click.Choice(['docker', 'cron', 'systemd', 'shell']), required=True, help='Deployment type')
@click.option('--remote-dir', default='/opt/apt-agent', help='Remote installation directory')
def deploy(name, target, ssh_key, deploy_type, remote_dir):
    """Deploy agent to remote server"""
    try:
        from performance.agents import AgentDeployer, DeploymentTarget, DeploymentMethod
        from pathlib import Path
        import asyncio
        
        # Find package directory
        package_dir = Path.home() / ".apt" / "agents" / name
        if not package_dir.exists():
            click.echo(f"❌ Agent package not found: {package_dir}", err=True)
            click.echo(f"   Create it first: aptcli agent create --name {name} ...", err=True)
            sys.exit(1)
        
        # Parse target
        deployment_target = DeploymentTarget.from_string(target, ssh_key)
        
        # Map string to enum
        method_map = {
            'docker': DeploymentMethod.DOCKER,
            'cron': DeploymentMethod.CRON,
            'systemd': DeploymentMethod.SYSTEMD,
            'shell': DeploymentMethod.SHELL
        }
        
        # Deploy
        deployer = AgentDeployer()
        success = asyncio.run(deployer.deploy(
            name,
            package_dir,
            deployment_target,
            method_map[deploy_type],
            remote_dir
        ))
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent.command()
@click.option('--name', help='Specific agent name')
@click.option('--endpoint', help='Agent endpoint URL')
@click.option('--auth-token', help='Authentication token')
def status(name, endpoint, auth_token):
    """Check agent health status"""
    try:
        import asyncio
        import aiohttp
        
        if not endpoint:
            click.echo("❌ --endpoint required (e.g., http://agent-host:9090)", err=True)
            sys.exit(1)
        
        async def check_health():
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        click.echo(f"✅ Agent: {data.get('agent_name', 'unknown')}")
                        click.echo(f"   Status: {data.get('status', 'unknown')}")
                        click.echo(f"   Mode: {data.get('mode', 'unknown')}")
                        click.echo(f"   Uptime: {data.get('uptime_seconds', 0):.1f}s")
                        click.echo(f"   Metrics: {data.get('metrics_count', 0)}")
                    else:
                        click.echo(f"❌ Health check failed: HTTP {resp.status}", err=True)
                        sys.exit(1)
        
        asyncio.run(check_health())
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--target', required=True, help='SSH target (user@host)')
@click.option('--ssh-key', help='Path to SSH private key')
@click.option('--type', 'deploy_type', type=click.Choice(['docker', 'cron', 'systemd', 'shell']), required=True, help='Deployment type')
@click.option('--tail', default=100, help='Number of lines to show')
def logs(name, target, ssh_key, deploy_type, tail):
    """Fetch agent logs from remote server"""
    try:
        from performance.agents import AgentDeployer, DeploymentTarget, DeploymentMethod
        import asyncio
        
        # Parse target
        deployment_target = DeploymentTarget.from_string(target, ssh_key)
        
        # Map string to enum
        method_map = {
            'docker': DeploymentMethod.DOCKER,
            'cron': DeploymentMethod.CRON,
            'systemd': DeploymentMethod.SYSTEMD,
            'shell': DeploymentMethod.SHELL
        }
        
        # Fetch logs
        deployer = AgentDeployer()
        logs_content = asyncio.run(deployer.get_logs(
            deployment_target,
            name,
            method_map[deploy_type],
            tail
        ))
        
        click.echo(logs_content)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent.command()
@click.option('--name', required=True, help='Agent name')
@click.option('--target', required=True, help='SSH target (user@host)')
@click.option('--ssh-key', help='Path to SSH private key')
@click.option('--type', 'deploy_type', type=click.Choice(['docker', 'cron', 'systemd', 'shell']), required=True, help='Deployment type')
@click.option('--cleanup', is_flag=True, help='Remove all agent files')
def remove(name, target, ssh_key, deploy_type, cleanup):
    """Remove an agent from remote server"""
    try:
        from performance.agents import AgentDeployer, DeploymentTarget, DeploymentMethod
        import asyncio
        
        # Confirm
        if not click.confirm(f"Remove agent '{name}' from {target}?"):
            click.echo("Cancelled")
            return
        
        # Parse target
        deployment_target = DeploymentTarget.from_string(target, ssh_key)
        
        # Map string to enum
        method_map = {
            'docker': DeploymentMethod.DOCKER,
            'cron': DeploymentMethod.CRON,
            'systemd': DeploymentMethod.SYSTEMD,
            'shell': DeploymentMethod.SHELL
        }
        
        # Remove
        deployer = AgentDeployer()
        success = asyncio.run(deployer.remove(
            deployment_target,
            name,
            method_map[deploy_type],
            cleanup
        ))
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def testbed():
    """Manage test infrastructure"""
    pass


@testbed.command()
@click.option('--config', required=True, type=click.Path(exists=True), help='Testbed configuration file')
def setup(config):
    """Setup testbed infrastructure (Phase 2 - Not yet implemented)"""
    click.echo("⚠️  This feature is planned for Phase 2")
    click.echo("\nFor now, deploy agents individually following:")
    click.echo("  docs/AGENT_DEPLOYMENT.md")


@cli.command()
@click.argument('test_file', type=click.Path(exists=True))
def run(test_file):
    """Run a test file"""
    click.echo(f"Running test: {test_file}")
    click.echo("\nℹ️  Use pytest to run tests:")
    click.echo(f"  pytest {test_file}")
    
    # Could implement actual test execution here
    import subprocess
    result = subprocess.run(['pytest', test_file])
    sys.exit(result.returncode)


@cli.command()
def version():
    """Show version information"""
    click.echo("aptcli version 1.0.0")
    click.echo("APT Framework - Allied Performance Testing")
    click.echo("\nPhase 1: Core functionality (YAML tests, agents)")
    click.echo("Phase 2: CLI automation (Planned)")


if __name__ == '__main__':
    cli()
