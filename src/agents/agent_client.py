"""
Agent Registry and Client - Manages connections to remote agents
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Type of agent"""
    REMOTE = "remote"
    BROWSER = "browser"


class AgentMode(Enum):
    """Agent operation mode"""
    EMIT = "emit"
    SERVE = "serve"


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    agent_id: str
    type: AgentType
    endpoint: str
    mode: AgentMode
    auth_token: Optional[str] = None
    timeout: int = 300
    health_check_interval: int = 60


class RemoteAgentClient:
    """Client for communicating with remote agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._healthy = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers
    
    async def health_check(self) -> bool:
        """
        Check if agent is healthy.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            async with self.session.get(
                f"{self.config.endpoint}/health",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._healthy = data.get('status') == 'healthy'
                    return self._healthy
                return False
        except Exception as e:
            logger.error(f"Health check failed for {self.config.agent_id}: {e}")
            self._healthy = False
            return False
    
    async def execute(
        self,
        code: str,
        context: Dict[str, Any] = None,
        tags: Dict[str, str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute code on the remote agent.
        
        Args:
            code: Python code to execute
            context: Context variables for execution
            tags: Tags for metrics
            timeout: Execution timeout (uses config default if None)
        
        Returns:
            Execution result with metrics
        
        Raises:
            Exception if execution fails
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        payload = {
            "code": code,
            "context": context or {},
            "tags": tags or {},
            "timeout": timeout or self.config.timeout
        }
        
        try:
            async with self.session.post(
                f"{self.config.endpoint}/execute",
                json=payload,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=timeout or self.config.timeout + 10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    raise Exception(f"Agent execution failed: {error_detail}")
        
        except asyncio.TimeoutError:
            raise Exception(f"Agent execution timeout after {timeout or self.config.timeout}s")
        except Exception as e:
            logger.error(f"Execution failed on {self.config.agent_id}: {e}")
            raise
    
    async def query_metrics(
        self,
        metric: Optional[str] = None,
        timerange: str = "last_1h",
        filters: Dict[str, Any] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query metrics from agent (serve mode only).
        
        Args:
            metric: Metric name to filter
            timerange: Time range for query
            filters: Additional filters
            limit: Maximum number of results
        
        Returns:
            List of metrics
        """
        if self.config.mode != AgentMode.SERVE:
            raise ValueError(f"Agent {self.config.agent_id} not in serve mode")
        
        params = {
            "metric": metric,
            "timerange": timerange,
            "filters": filters or {},
            "limit": limit
        }
        
        try:
            async with self.session.get(
                f"{self.config.endpoint}/metrics",
                params=params,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('metrics', [])
                else:
                    error_detail = await response.text()
                    raise Exception(f"Metrics query failed: {error_detail}")
        
        except Exception as e:
            logger.error(f"Metrics query failed on {self.config.agent_id}: {e}")
            raise


class AgentRegistry:
    """Registry for managing multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, RemoteAgentClient] = {}
        self.configs: Dict[str, AgentConfig] = {}
    
    def register(self, config: AgentConfig):
        """
        Register an agent.
        
        Args:
            config: Agent configuration
        """
        self.configs[config.agent_id] = config
        logger.info(f"Registered agent: {config.agent_id} ({config.type.value})")
    
    async def get_client(self, agent_id: str) -> RemoteAgentClient:
        """
        Get or create client for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Agent client
        
        Raises:
            KeyError if agent not registered
        """
        if agent_id not in self.configs:
            raise KeyError(f"Agent '{agent_id}' not registered")
        
        if agent_id not in self.agents:
            config = self.configs[agent_id]
            client = RemoteAgentClient(config)
            await client.__aenter__()  # Initialize session
            self.agents[agent_id] = client
        
        return self.agents[agent_id]
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all registered agents.
        
        Returns:
            Dict mapping agent_id to health status
        """
        results = {}
        for agent_id in self.configs:
            try:
                client = await self.get_client(agent_id)
                results[agent_id] = await client.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {agent_id}: {e}")
                results[agent_id] = False
        
        return results
    
    async def cleanup(self):
        """Cleanup all agent connections"""
        for client in self.agents.values():
            await client.__aexit__(None, None, None)
        self.agents.clear()
    
    def list_agents(self) -> List[str]:
        """Get list of registered agent IDs"""
        return list(self.configs.keys())
