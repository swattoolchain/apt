"""
Async Agent Client for QPT

Handles asynchronous job submission and polling for remote agent execution.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)


class AsyncAgentClient:
    """Client for async job execution on remote agents"""
    
    def __init__(self, endpoint: str, auth_token: str = None, 
                 rampup_seconds: int = 5, polling_frequency: int = 2,
                 timeout: int = 300, max_retries: int = 3):
        """
        Initialize async agent client.
        
        Args:
            endpoint: Agent endpoint URL
            auth_token: Authentication token
            rampup_seconds: Initial delay before first poll
            polling_frequency: Seconds between polls
            timeout: Maximum time to wait for completion
            max_retries: Maximum retry attempts for failed polls
        """
        self.endpoint = endpoint.rstrip('/')
        self.auth_token = auth_token
        self.rampup_seconds = rampup_seconds
        self.polling_frequency = polling_frequency
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.headers = {}
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
    
    async def submit_job(self, code: str, context: Dict[str, Any] = None,
                        timeout: int = None, priority: int = 5,
                        tags: Dict[str, str] = None) -> str:
        """
        Submit a job for async execution.
        
        Args:
            code: Python code to execute
            context: Execution context
            timeout: Job timeout (overrides client timeout)
            priority: Job priority (1-10)
            tags: Optional tags
            
        Returns:
            job_id: Unique job identifier
        """
        url = f"{self.endpoint}/jobs"
        
        payload = {
            "code": code,
            "context": context or {},
            "timeout": timeout or self.timeout,
            "priority": priority,
            "tags": tags or {}
        }
        
        logger.info(f"📤 Submitting async job to {url}")
        logger.debug(f"   Priority: {priority}, Timeout: {timeout or self.timeout}s")
        logger.debug(f"   Tags: {tags}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Job submission failed: {response.status} - {error_text}")
                    raise Exception(f"Failed to submit job: {response.status} - {error_text}")
                
                result = await response.json()
                job_id = result.get('job_id')
                
                logger.info(f"✅ Job submitted successfully: {job_id}")
                logger.info(f"   Status: {result.get('status')}")
                logger.info(f"   Message: {result.get('message')}")
                return job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the current status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary
        """
        url = f"{self.endpoint}/jobs/{job_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get job status: {response.status} - {error_text}")
                
                return await response.json()
    
    async def get_job_logs(self, job_id: str) -> str:
        """
        Get execution logs for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Log contents as string
        """
        url = f"{self.endpoint}/jobs/{job_id}/logs"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get job logs: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get('logs', '')
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        url = f"{self.endpoint}/jobs/{job_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=self.headers) as response:
                return response.status == 200
    
    async def execute_and_wait(self, code: str, context: Dict[str, Any] = None,
                              timeout: int = None, priority: int = 5,
                              tags: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Submit a job and wait for completion with polling.
        
        This is the main method for async execution. It:
        1. Submits the job
        2. Waits for rampup period
        3. Polls for status until completion or timeout
        4. Returns the result
        
        Args:
            code: Python code to execute
            context: Execution context
            timeout: Job timeout
            priority: Job priority
            tags: Optional tags
            
        Returns:
            Execution result dictionary with status, result, duration, etc.
        """
        # Submit job
        job_id = await self.submit_job(code, context, timeout, priority, tags)
        
        # Initial rampup delay
        logger.info(f"Job {job_id}: Waiting {self.rampup_seconds}s before first poll (rampup)")
        await asyncio.sleep(self.rampup_seconds)
        
        # Polling loop
        start_time = time.time()
        poll_count = 0
        retry_count = 0
        
        while True:
            elapsed = time.time() - start_time
            
            # Check timeout
            if self.timeout > 0 and elapsed > self.timeout:
                logger.warning(f"Job {job_id}: Timeout after {elapsed:.1f}s")
                # Try to cancel the job
                await self.cancel_job(job_id)
                raise TimeoutError(f"Job {job_id} exceeded timeout of {self.timeout}s")
            
            try:
                # Poll for status
                poll_count += 1
                status = await self.get_job_status(job_id)
                job_status = status.get('status')
                
                logger.info(f"🔍 Job {job_id}: Poll #{poll_count}")
                logger.info(f"   Status: {job_status}")
                logger.info(f"   Elapsed: {elapsed:.1f}s")
                if job_status == 'running':
                    logger.info(f"   ⏳ Job is running...")
                elif job_status == 'pending':
                    logger.info(f"   ⏸️  Job is pending in queue...")
                
                # Check if job is complete
                if job_status in ['completed', 'failed', 'cancelled', 'timeout']:
                    logger.info(f"")
                    logger.info(f"{'='*60}")
                    status_str = (job_status or "UNKNOWN").upper()
                    logger.info(f"🏁 Job {job_id}: {status_str}")
                    logger.info(f"   Total Duration: {elapsed:.1f}s")
                    logger.info(f"   Total Polls: {poll_count}")
                    
                    job_duration = status.get('duration')
                    if job_duration is not None:
                        logger.info(f"   Execution Duration: {job_duration:.2f}s")
                    
                    logger.info(f"{'='*60}")
                    logger.info(f"")
                    
                    # Get logs if available
                    try:
                        logger.info(f"📄 Retrieving job logs...")
                        logs = await self.get_job_logs(job_id)
                        status['logs'] = logs
                        if logs:
                            logger.info(f"✅ Logs retrieved ({len(logs)} bytes)")
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to retrieve logs for job {job_id}: {e}")

                    
                    # Return result
                    if job_status == 'completed':
                        return {
                            'status': 'success',
                            'result': status.get('result'),
                            'duration': status.get('duration'),
                            'total_duration': elapsed,
                            'job_id': job_id,
                            'polls': poll_count,
                            'logs': status.get('logs')
                        }
                    else:
                        # Failed, cancelled, or timeout
                        return {
                            'status': 'error',
                            'error': status.get('error', f'Job {job_status}'),
                            'duration': status.get('duration'),
                            'total_duration': elapsed,
                            'job_id': job_id,
                            'job_status': job_status,
                            'polls': poll_count,
                            'logs': status.get('logs')
                        }
                
                # Job still running, wait before next poll
                retry_count = 0  # Reset retry count on successful poll
                await asyncio.sleep(self.polling_frequency)
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"Job {job_id}: Poll failed (attempt {retry_count}/{self.max_retries}): {e}")
                
                if retry_count >= self.max_retries:
                    logger.error(f"Job {job_id}: Max retries exceeded")
                    raise Exception(f"Failed to poll job {job_id} after {self.max_retries} retries: {e}")
                
                # Exponential backoff
                backoff = self.polling_frequency * (2 ** (retry_count - 1))
                await asyncio.sleep(backoff)


def load_execution_config() -> Dict[str, Any]:
    """Load execution configuration from config/execution_config.yml"""
    import yaml
    
    config_file = Path("config/execution_config.yml")
    if not config_file.exists():
        logger.warning("execution_config.yml not found, using defaults")
        return {
            'execution_mode': 'sync',
            'async_config': {
                'rampup_seconds': 5,
                'polling_frequency': 2,
                'timeout': 300,
                'max_poll_retries': 3
            }
        }
    
    with open(config_file) as f:
        return yaml.safe_load(f)


def create_async_client(endpoint: str, auth_token: str = None,
                       config: Dict[str, Any] = None) -> AsyncAgentClient:
    """
    Create an async agent client with configuration.
    
    Args:
        endpoint: Agent endpoint URL
        auth_token: Authentication token
        config: Execution configuration (loaded from execution_config.yml if None)
        
    Returns:
        Configured AsyncAgentClient instance
    """
    if config is None:
        config = load_execution_config()
    
    async_config = config.get('async_config', {})
    
    return AsyncAgentClient(
        endpoint=endpoint,
        auth_token=auth_token,
        rampup_seconds=async_config.get('rampup_seconds', 5),
        polling_frequency=async_config.get('polling_frequency', 2),
        timeout=async_config.get('timeout', 300),
        max_retries=async_config.get('max_poll_retries', 3)
    )
