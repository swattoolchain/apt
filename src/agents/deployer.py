"""
Agent Deployer - Deploy agents to remote servers via SSH

Handles SSH connection, file transfer, and remote execution for agent deployment.
"""

import asyncio
import asyncssh
from pathlib import Path
from typing import Dict, Optional
import logging

from .provisioner import DeploymentMethod

logger = logging.getLogger(__name__)


class DeploymentTarget:
    """SSH deployment target"""
    
    def __init__(self, host: str, user: str, port: int = 22, key_file: Optional[str] = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_file = key_file
    
    @classmethod
    def from_string(cls, target: str, key_file: Optional[str] = None):
        """
        Parse SSH target string.
        
        Format: [user@]host[:port]
        Example: ubuntu@ec2-server.com:22
        """
        user = "root"
        host = target
        port = 22
        
        if "@" in target:
            user, host = target.split("@", 1)
        
        if ":" in host:
            host, port_str = host.rsplit(":", 1)
            port = int(port_str)
        
        return cls(host, user, port, key_file)


class AgentDeployer:
    """Deploy agents to remote servers"""
    
    def __init__(self):
        self.conn: Optional[asyncssh.SSHClientConnection] = None
    
    async def deploy(
        self,
        agent_name: str,
        package_dir: Path,
        target: DeploymentTarget,
        deployment_method: DeploymentMethod,
        remote_dir: str = "/opt/apt-agent"
    ) -> bool:
        """
        Deploy agent package to remote server.
        
        Args:
            agent_name: Agent name
            package_dir: Local package directory
            target: Deployment target
            deployment_method: Deployment method
            remote_dir: Remote installation directory
        
        Returns:
            True if deployment successful
        """
        try:
            print(f"🚀 Deploying agent '{agent_name}' to {target.user}@{target.host}...")
            
            # Connect to remote server
            await self._connect(target)
            
            # Create remote directory
            await self._run_command(f"mkdir -p {remote_dir}")
            
            # Transfer files
            print(f"📦 Transferring files...")
            await self._transfer_directory(package_dir, remote_dir)
            
            # Execute deployment based on method
            if deployment_method == DeploymentMethod.DOCKER:
                await self._deploy_docker(remote_dir)
            elif deployment_method == DeploymentMethod.CRON:
                await self._deploy_cron(remote_dir)
            elif deployment_method == DeploymentMethod.SYSTEMD:
                await self._deploy_systemd(remote_dir, agent_name)
            elif deployment_method == DeploymentMethod.SHELL:
                await self._deploy_shell(remote_dir)
            
            # Verify deployment
            print(f"✅ Verifying deployment...")
            success = await self._verify_deployment(remote_dir)
            
            if success:
                print(f"✅ Agent '{agent_name}' deployed successfully!")
            else:
                print(f"⚠️  Agent deployed but verification failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            print(f"❌ Deployment failed: {e}")
            return False
        
        finally:
            await self._disconnect()
    
    async def _connect(self, target: DeploymentTarget):
        """Establish SSH connection"""
        try:
            connect_kwargs = {
                'host': target.host,
                'port': target.port,
                'username': target.user,
                'known_hosts': None  # Accept any host key (use with caution)
            }
            
            if target.key_file:
                connect_kwargs['client_keys'] = [target.key_file]
            
            self.conn = await asyncssh.connect(**connect_kwargs)
            print(f"✅ Connected to {target.user}@{target.host}")
            
        except Exception as e:
            raise Exception(f"SSH connection failed: {e}")
    
    async def _disconnect(self):
        """Close SSH connection"""
        if self.conn:
            self.conn.close()
            await self.conn.wait_closed()
    
    async def _run_command(self, command: str, check: bool = True) -> str:
        """
        Execute command on remote server.
        
        Args:
            command: Command to execute
            check: Raise exception on non-zero exit code
        
        Returns:
            Command output
        """
        if not self.conn:
            raise Exception("Not connected to remote server")
        
        result = await self.conn.run(command, check=check)
        return result.stdout
    
    async def _transfer_directory(self, local_dir: Path, remote_dir: str):
        """Transfer directory to remote server"""
        if not self.conn:
            raise Exception("Not connected to remote server")
        
        async with self.conn.start_sftp_client() as sftp:
            # Transfer all files in directory
            for local_file in local_dir.rglob('*'):
                if local_file.is_file():
                    # Calculate relative path
                    rel_path = local_file.relative_to(local_dir)
                    remote_file = f"{remote_dir}/{rel_path}"
                    
                    # Create remote directory if needed
                    remote_file_dir = str(Path(remote_file).parent)
                    await self._run_command(f"mkdir -p {remote_file_dir}", check=False)
                    
                    # Upload file
                    await sftp.put(str(local_file), remote_file)
                    
                    # Preserve execute permissions
                    if local_file.stat().st_mode & 0o111:
                        await self._run_command(f"chmod +x {remote_file}")
    
    async def _deploy_docker(self, remote_dir: str):
        """Deploy Docker agent"""
        print("🐳 Deploying Docker agent...")
        
        # Check if Docker is installed
        try:
            await self._run_command("which docker")
        except:
            raise Exception("Docker not installed on remote server")
        
        # Check if docker-compose is installed
        try:
            await self._run_command("which docker-compose")
            compose_cmd = "docker-compose"
        except:
            # Try docker compose (v2)
            try:
                await self._run_command("docker compose version")
                compose_cmd = "docker compose"
            except:
                raise Exception("docker-compose not installed on remote server")
        
        # Build and start
        await self._run_command(f"cd {remote_dir} && {compose_cmd} build")
        await self._run_command(f"cd {remote_dir} && {compose_cmd} up -d")
        
        print("✅ Docker agent started")
    
    async def _deploy_cron(self, remote_dir: str):
        """Deploy cron agent"""
        print("⏰ Deploying cron agent...")
        
        # Setup virtual environment
        await self._run_command(f"cd {remote_dir} && python3 -m venv venv")
        await self._run_command(
            f"cd {remote_dir} && source venv/bin/activate && pip install -r requirements.txt"
        )
        
        # Install crontab
        crontab_file = f"{remote_dir}/crontab.txt"
        await self._run_command(
            f"(crontab -l 2>/dev/null; cat {crontab_file}) | crontab -"
        )
        
        print("✅ Cron agent installed")
    
    async def _deploy_systemd(self, remote_dir: str, agent_name: str):
        """Deploy systemd agent"""
        print("⚙️  Deploying systemd agent...")
        
        # Run install script
        await self._run_command(f"cd {remote_dir} && sudo ./install.sh")
        
        print("✅ Systemd agent installed and started")
    
    async def _deploy_shell(self, remote_dir: str):
        """Deploy shell agent"""
        print("🔧 Deploying shell agent...")
        
        # Make script executable
        await self._run_command(f"chmod +x {remote_dir}/start_agent.sh")
        
        # Start agent in background
        await self._run_command(
            f"cd {remote_dir} && nohup ./start_agent.sh > agent.log 2>&1 &"
        )
        
        print("✅ Shell agent started")
    
    async def _verify_deployment(self, remote_dir: str) -> bool:
        """Verify agent is running"""
        try:
            # Wait a bit for agent to start
            await asyncio.sleep(3)
            
            # Try to curl health endpoint
            result = await self._run_command(
                "curl -s http://localhost:9090/health",
                check=False
            )
            
            return "healthy" in result.lower()
        
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return False
    
    async def get_logs(
        self,
        target: DeploymentTarget,
        agent_name: str,
        deployment_method: DeploymentMethod,
        tail: int = 100
    ) -> str:
        """
        Fetch agent logs from remote server.
        
        Args:
            target: Deployment target
            agent_name: Agent name
            deployment_method: Deployment method
            tail: Number of lines to fetch
        
        Returns:
            Log content
        """
        try:
            await self._connect(target)
            
            if deployment_method == DeploymentMethod.DOCKER:
                logs = await self._run_command(
                    f"docker logs {agent_name} --tail {tail}",
                    check=False
                )
            elif deployment_method == DeploymentMethod.SYSTEMD:
                logs = await self._run_command(
                    f"sudo journalctl -u {agent_name} -n {tail}",
                    check=False
                )
            else:
                logs = await self._run_command(
                    f"tail -n {tail} /opt/apt-agent/agent.log",
                    check=False
                )
            
            return logs
        
        finally:
            await self._disconnect()
    
    async def remove(
        self,
        target: DeploymentTarget,
        agent_name: str,
        deployment_method: DeploymentMethod,
        cleanup: bool = False
    ) -> bool:
        """
        Remove agent from remote server.
        
        Args:
            target: Deployment target
            agent_name: Agent name
            deployment_method: Deployment method
            cleanup: Remove all files
        
        Returns:
            True if successful
        """
        try:
            await self._connect(target)
            
            print(f"🗑️  Removing agent '{agent_name}'...")
            
            if deployment_method == DeploymentMethod.DOCKER:
                await self._run_command(
                    f"cd /opt/apt-agent && docker-compose down",
                    check=False
                )
                if cleanup:
                    await self._run_command("docker rmi $(docker images -q apt-agent)", check=False)
            
            elif deployment_method == DeploymentMethod.SYSTEMD:
                await self._run_command(f"sudo systemctl stop {agent_name}", check=False)
                await self._run_command(f"sudo systemctl disable {agent_name}", check=False)
                await self._run_command(f"sudo rm /etc/systemd/system/{agent_name}.service", check=False)
                await self._run_command("sudo systemctl daemon-reload", check=False)
            
            elif deployment_method == DeploymentMethod.CRON:
                await self._run_command(
                    f"crontab -l | grep -v '{agent_name}' | crontab -",
                    check=False
                )
            
            if cleanup:
                await self._run_command("rm -rf /opt/apt-agent", check=False)
            
            print(f"✅ Agent removed")
            return True
        
        except Exception as e:
            logger.error(f"Removal failed: {e}")
            return False
        
        finally:
            await self._disconnect()
