"""
Agent Health Monitor - Continuous health checking with auto-recovery
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

from .agent_client import AgentRegistry

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class AgentHealthMonitor:
    """
    Monitor agent health and connectivity with auto-recovery.
    
    Features:
    - Continuous health checks
    - Failure detection and alerting
    - Uptime tracking
    - Auto-recovery attempts
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.agent_states: Dict[str, Dict] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
    
    async def start(self):
        """Start monitoring all registered agents"""
        self._running = True
        
        for agent_id in self.registry.list_agents():
            await self.start_monitoring(agent_id)
        
        logger.info(f"Health monitoring started for {len(self.monitoring_tasks)} agents")
    
    async def stop(self):
        """Stop all monitoring tasks"""
        self._running = False
        
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("Health monitoring stopped")
    
    async def start_monitoring(self, agent_id: str):
        """
        Start health monitoring for a specific agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self.monitoring_tasks:
            logger.warning(f"Already monitoring agent: {agent_id}")
            return
        
        # Initialize state
        self.agent_states[agent_id] = {
            'status': AgentStatus.UNKNOWN,
            'last_check': None,
            'last_success': None,
            'consecutive_failures': 0,
            'total_checks': 0,
            'total_failures': 0,
            'uptime_percentage': 0.0,
            'last_error': None
        }
        
        # Start monitoring loop
        task = asyncio.create_task(self._monitor_loop(agent_id))
        self.monitoring_tasks[agent_id] = task
        
        logger.info(f"Started monitoring agent: {agent_id}")
    
    async def _monitor_loop(self, agent_id: str):
        """
        Continuous health check loop for an agent.
        
        Args:
            agent_id: Agent identifier
        """
        # Get configuration from registry
        config = self.registry.configs.get(agent_id)
        if not config:
            logger.error(f"No config found for agent: {agent_id}")
            return
        
        interval = config.health_check_interval
        max_failures = 3  # Alert threshold
        
        while self._running:
            try:
                # Perform health check
                client = await self.registry.get_client(agent_id)
                is_healthy = await client.health_check()
                
                state = self.agent_states[agent_id]
                state['last_check'] = datetime.now()
                state['total_checks'] += 1
                
                if is_healthy:
                    # Agent is healthy
                    if state['status'] != AgentStatus.HEALTHY:
                        logger.info(f"Agent {agent_id} recovered")
                    
                    state['status'] = AgentStatus.HEALTHY
                    state['last_success'] = datetime.now()
                    state['consecutive_failures'] = 0
                    state['last_error'] = None
                else:
                    # Agent is degraded/failed
                    state['consecutive_failures'] += 1
                    state['total_failures'] += 1
                    
                    if state['consecutive_failures'] >= max_failures:
                        state['status'] = AgentStatus.FAILED
                        await self._alert_failure(agent_id, state)
                    else:
                        state['status'] = AgentStatus.DEGRADED
                
                # Update uptime percentage
                if state['total_checks'] > 0:
                    successful_checks = state['total_checks'] - state['total_failures']
                    state['uptime_percentage'] = (successful_checks / state['total_checks']) * 100
            
            except Exception as e:
                # Health check failed
                state = self.agent_states[agent_id]
                state['status'] = AgentStatus.FAILED
                state['consecutive_failures'] += 1
                state['total_failures'] += 1
                state['last_error'] = str(e)
                
                logger.error(f"Health check error for {agent_id}: {e}")
                
                if state['consecutive_failures'] >= max_failures:
                    await self._alert_failure(agent_id, state)
            
            # Wait before next check
            await asyncio.sleep(interval)
    
    async def _alert_failure(self, agent_id: str, state: Dict):
        """
        Alert on agent failure.
        
        Args:
            agent_id: Agent identifier
            state: Current agent state
        """
        logger.error(
            f"🚨 ALERT: Agent '{agent_id}' has failed "
            f"{state['consecutive_failures']} consecutive health checks"
        )
        logger.error(f"   Last error: {state.get('last_error', 'Unknown')}")
        logger.error(f"   Uptime: {state.get('uptime_percentage', 0):.2f}%")
        
        # TODO: Integrate with alerting systems
        # - Email notifications
        # - Slack/Teams webhooks
        # - PagerDuty
        # - Custom webhooks
    
    def get_status(self, agent_id: str) -> Dict:
        """
        Get current status of an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Agent status dictionary
        """
        if agent_id not in self.agent_states:
            return {
                'status': AgentStatus.UNKNOWN.value,
                'message': f'Agent {agent_id} not being monitored'
            }
        
        state = self.agent_states[agent_id].copy()
        state['status'] = state['status'].value  # Convert enum to string
        
        # Format timestamps
        if state['last_check']:
            state['last_check'] = state['last_check'].isoformat()
        if state['last_success']:
            state['last_success'] = state['last_success'].isoformat()
        
        return state
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        Get status of all monitored agents.
        
        Returns:
            Dict mapping agent_id to status
        """
        return {
            agent_id: self.get_status(agent_id)
            for agent_id in self.agent_states
        }
    
    def get_healthy_agents(self) -> list[str]:
        """Get list of healthy agent IDs"""
        return [
            agent_id
            for agent_id, state in self.agent_states.items()
            if state['status'] == AgentStatus.HEALTHY
        ]
    
    def get_failed_agents(self) -> list[str]:
        """Get list of failed agent IDs"""
        return [
            agent_id
            for agent_id, state in self.agent_states.items()
            if state['status'] == AgentStatus.FAILED
        ]
