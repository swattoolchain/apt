"""
Async Agent Client - Handles long-running tests properly
Uses job-based pattern instead of long-lived HTTP connections
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AsyncAgentClient:
    """Client for async job-based agent communication."""
    
    def __init__(self, endpoint: str, auth_token: Optional[str] = None):
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def execute_async(
        self,
        code: str,
        context: Dict[str, Any] = None,
        timeout: int = 1800,
        poll_interval: int = 30,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Execute code asynchronously with polling.
        
        Args:
            code: Code to execute
            context: Execution context
            timeout: Maximum execution time
            poll_interval: How often to poll for status (seconds)
            progress_callback: Optional callback for progress updates
        
        Returns:
            Execution results
        """
        # Step 1: Start async job
        logger.info("Starting async job...")
        job_id = await self._start_job(code, context, timeout)
        logger.info(f"Job started: {job_id}")
        
        # Step 2: Poll for completion
        logger.info(f"Polling every {poll_interval}s...")
        result = await self._poll_until_complete(
            job_id,
            poll_interval,
            timeout,
            progress_callback
        )
        
        # Step 3: Cleanup (optional)
        # await self._delete_job(job_id)
        
        return result
    
    async def _start_job(
        self,
        code: str,
        context: Dict[str, Any],
        timeout: int
    ) -> str:
        """Start async job, returns job_id."""
        payload = {
            "code": code,
            "context": context or {},
            "timeout": timeout
        }
        
        async with self.session.post(
            f"{self.endpoint}/execute/async",
            json=payload,
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=30)  # ← Short timeout!
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"Failed to start job: {error}")
            
            data = await response.json()
            return data["job_id"]
    
    async def _poll_until_complete(
        self,
        job_id: str,
        poll_interval: int,
        max_wait: int,
        progress_callback=None
    ) -> Dict[str, Any]:
        """Poll job status until complete."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if we've exceeded max wait time
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"Job timeout after {max_wait}s")
            
            # Get job status
            status = await self._get_job_status(job_id)
            
            logger.info(
                f"Job {job_id}: {status['status']} "
                f"({status.get('progress', 0):.1f}%)"
            )
            
            # Call progress callback if provided
            if progress_callback and status.get('progress'):
                progress_callback(status['progress'])
            
            # Check if complete
            if status['status'] == 'complete':
                logger.info(f"Job {job_id} complete!")
                return await self._get_job_results(job_id)
            
            if status['status'] == 'failed':
                raise Exception(f"Job failed: {status.get('message')}")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
    
    async def _get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        async with self.session.get(
            f"{self.endpoint}/jobs/{job_id}",
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=10)  # ← Short timeout!
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"Failed to get status: {error}")
            
            return await response.json()
    
    async def _get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get job results."""
        async with self.session.get(
            f"{self.endpoint}/jobs/{job_id}/results",
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=60)  # ← Short timeout!
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"Failed to get results: {error}")
            
            return await response.json()
    
    async def _delete_job(self, job_id: str):
        """Delete job (cleanup)."""
        async with self.session.delete(
            f"{self.endpoint}/jobs/{job_id}",
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status != 200:
                logger.warning(f"Failed to delete job {job_id}")
    
    async def execute_sync(
        self,
        code: str,
        context: Dict[str, Any] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute code synchronously (for short tests < 5 minutes).
        Use execute_async() for longer tests.
        """
        if timeout > 300:
            logger.warning(
                f"Timeout {timeout}s > 300s. "
                "Consider using execute_async() instead."
            )
        
        payload = {
            "code": code,
            "context": context or {},
            "timeout": timeout
        }
        
        async with self.session.post(
            f"{self.endpoint}/execute",
            json=payload,
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=timeout + 10)
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"Execution failed: {error}")
            
            return await response.json()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def example_usage():
    """Example of how to use the async client."""
    
    # Create client
    async with AsyncAgentClient(
        endpoint="http://vm1:9090",
        auth_token="your-token"
    ) as client:
        
        # For SHORT tests (< 5 minutes) - use sync
        print("Running short test...")
        result = await client.execute_sync(
            code="import time; time.sleep(60); result = {'test': 'done'}",
            timeout=120
        )
        print(f"Short test result: {result}")
        
        # For LONG tests (> 5 minutes) - use async with polling
        print("\nRunning long test...")
        
        def progress_update(progress):
            print(f"Progress: {progress:.1f}%")
        
        result = await client.execute_async(
            code="""
import subprocess
result = subprocess.run(
    ['k6', 'run', '--duration', '30m', 'script.js'],
    capture_output=True
)
            """,
            timeout=1800,  # 30 minutes
            poll_interval=30,  # Poll every 30 seconds
            progress_callback=progress_update
        )
        print(f"Long test result: {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())
