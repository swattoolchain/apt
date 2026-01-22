"""
Enhanced Agent Server with Async Job Support and Job Queue
Handles long-running tests properly for AWS/cloud environments
Features:
- Job queuing with configurable concurrency limit
- Automatic job scheduling
- Priority-based execution
- Resource management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
import time
import asyncio
from datetime import datetime
from enum import Enum
from collections import deque
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ============================================================================
# CONFIGURATION
# ============================================================================

class AgentConfig(BaseModel):
    """Agent configuration loaded from config.json"""
    agent_id: str
    mode: str = "serve"
    port: int = 9090
    auth_token: Optional[str] = None
    max_concurrent_jobs: int = Field(default=3, description="Maximum concurrent jobs")
    max_queued_jobs: int = Field(default=10, description="Maximum queued jobs")
    job_timeout: int = Field(default=3600, description="Default job timeout")
    allowed_modules: List[str] = []

# Load config
config_path = os.getenv("AGENT_CONFIG_PATH", "config.json")
try:
    with open(config_path) as f:
        config_data = json.load(f)
        AGENT_CONFIG = AgentConfig(**config_data)
        logger.info(f"Loaded config: max_concurrent_jobs={AGENT_CONFIG.max_concurrent_jobs}")
except FileNotFoundError:
    logger.warning("No config.json found, using defaults")
    AGENT_CONFIG = AgentConfig(agent_id="default-agent")

# ============================================================================
# JOB MANAGEMENT
# ============================================================================

class JobStatus(str, Enum):
    QUEUED = "queued"
    PENDING = "pending"  # Ready to run
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class ExecuteRequest(BaseModel):
    code: str
    context: Dict[str, Any] = {}
    timeout: int = 300
    priority: JobPriority = JobPriority.NORMAL


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    queue_position: Optional[int] = None


# Job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

# Job queue (priority queue)
job_queue: deque = deque()

# Currently running jobs
running_jobs: Dict[str, asyncio.Task] = {}

# Job scheduler lock
scheduler_lock = asyncio.Lock()


# ============================================================================
# JOB SCHEDULER
# ============================================================================

async def schedule_jobs():
    """Background task to schedule queued jobs."""
    while True:
        async with scheduler_lock:
            # Check if we can run more jobs
            current_running = len(running_jobs)
            available_slots = AGENT_CONFIG.max_concurrent_jobs - current_running
            
            if available_slots > 0 and job_queue:
                # Get jobs to run (sorted by priority)
                jobs_to_run = []
                
                # Sort queue by priority (higher first)
                sorted_queue = sorted(
                    job_queue,
                    key=lambda jid: jobs[jid].get("priority", 0),
                    reverse=True
                )
                
                for job_id in sorted_queue[:available_slots]:
                    jobs_to_run.append(job_id)
                    job_queue.remove(job_id)
                
                # Start jobs
                for job_id in jobs_to_run:
                    logger.info(f"Starting job {job_id} from queue")
                    task = asyncio.create_task(_execute_job(job_id))
                    running_jobs[job_id] = task
                    jobs[job_id]["status"] = JobStatus.RUNNING
                    jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Sleep before next check
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    """Start background scheduler on startup."""
    asyncio.create_task(schedule_jobs())
    logger.info(f"Agent started: {AGENT_CONFIG.agent_id}")
    logger.info(f"Max concurrent jobs: {AGENT_CONFIG.max_concurrent_jobs}")
    logger.info(f"Max queued jobs: {AGENT_CONFIG.max_queued_jobs}")


# ============================================================================
# SYNCHRONOUS ENDPOINT (for short tests < 5 minutes)
# ============================================================================

@app.post("/execute")
async def execute_sync(request: ExecuteRequest):
    """
    Synchronous execution (for short tests only).
    Use /execute/async for tests > 5 minutes.
    """
    if request.timeout > 300:
        raise HTTPException(
            status_code=400,
            detail="Use /execute/async for tests longer than 5 minutes"
        )
    
    # Execute code synchronously
    result = _execute_code(request.code, request.context, request.timeout)
    return result


# ============================================================================
# ASYNC ENDPOINTS (for long tests - RECOMMENDED)
# ============================================================================

@app.post("/execute/async", response_model=JobResponse)
async def execute_async(request: ExecuteRequest):
    """
    Start async execution (recommended for long tests).
    Returns job_id immediately, poll /jobs/{job_id} for status.
    
    Jobs are queued if max_concurrent_jobs limit is reached.
    """
    # Check queue limit
    total_jobs = len(running_jobs) + len(job_queue)
    if total_jobs >= AGENT_CONFIG.max_concurrent_jobs + AGENT_CONFIG.max_queued_jobs:
        raise HTTPException(
            status_code=429,
            detail=f"Job queue full. Max: {AGENT_CONFIG.max_queued_jobs} queued + "
                   f"{AGENT_CONFIG.max_concurrent_jobs} running"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    jobs[job_id] = {
        "status": JobStatus.QUEUED,
        "created_at": datetime.now().isoformat(),
        "code": request.code,
        "context": request.context,
        "timeout": request.timeout,
        "priority": request.priority.value,
        "result": None,
        "error": None,
        "progress": 0.0,
        "started_at": None,
        "completed_at": None
    }
    
    # Add to queue
    async with scheduler_lock:
        job_queue.append(job_id)
        queue_position = len(job_queue)
    
    logger.info(
        f"Job {job_id} queued (priority: {request.priority.name}, "
        f"position: {queue_position}, "
        f"running: {len(running_jobs)}/{AGENT_CONFIG.max_concurrent_jobs})"
    )
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=jobs[job_id]["created_at"],
        queue_position=queue_position,
        message=f"Job queued (position: {queue_position})"
    )


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status and progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Calculate queue position if queued
    queue_position = None
    if job["status"] == JobStatus.QUEUED:
        async with scheduler_lock:
            if job_id in job_queue:
                # Sort by priority to get accurate position
                sorted_queue = sorted(
                    job_queue,
                    key=lambda jid: jobs[jid].get("priority", 0),
                    reverse=True
                )
                queue_position = sorted_queue.index(job_id) + 1
    
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        progress=job.get("progress"),
        queue_position=queue_position,
        message=_get_job_message(job, queue_position)
    )


@app.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """Get job results (only available when complete)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] == JobStatus.RUNNING:
        raise HTTPException(status_code=425, detail="Job still running")
    
    if job["status"] == JobStatus.QUEUED:
        raise HTTPException(status_code=425, detail="Job still queued")
    
    if job["status"] == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=job["error"])
    
    if job["status"] != JobStatus.COMPLETE:
        raise HTTPException(status_code=400, detail=f"Job status: {job['status']}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "execution_time": job.get("execution_time"),
        "completed_at": job["completed_at"]
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete job and its results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove from queue if queued
    async with scheduler_lock:
        if job_id in job_queue:
            job_queue.remove(job_id)
    
    # Cancel if running
    if job_id in running_jobs:
        running_jobs[job_id].cancel()
        del running_jobs[job_id]
    
    del jobs[job_id]
    return {"message": "Job deleted"}


@app.get("/jobs")
async def list_jobs():
    """List all jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "created_at": job["created_at"],
                "progress": job.get("progress"),
                "priority": job.get("priority", 1)
            }
            for job_id, job in jobs.items()
        ],
        "stats": {
            "queued": len(job_queue),
            "running": len(running_jobs),
            "max_concurrent": AGENT_CONFIG.max_concurrent_jobs,
            "max_queued": AGENT_CONFIG.max_queued_jobs
        }
    }


@app.get("/stats")
async def get_stats():
    """Get agent statistics."""
    return {
        "agent_id": AGENT_CONFIG.agent_id,
        "max_concurrent_jobs": AGENT_CONFIG.max_concurrent_jobs,
        "max_queued_jobs": AGENT_CONFIG.max_queued_jobs,
        "current_running": len(running_jobs),
        "current_queued": len(job_queue),
        "available_slots": AGENT_CONFIG.max_concurrent_jobs - len(running_jobs),
        "total_jobs": len(jobs),
        "jobs_by_status": {
            "queued": len([j for j in jobs.values() if j["status"] == JobStatus.QUEUED]),
            "running": len([j for j in jobs.values() if j["status"] == JobStatus.RUNNING]),
            "complete": len([j for j in jobs.values() if j["status"] == JobStatus.COMPLETE]),
            "failed": len([j for j in jobs.values() if j["status"] == JobStatus.FAILED])
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _execute_job(job_id: str):
    """Execute job in background."""
    job = jobs[job_id]
    
    try:
        # Update status
        job["status"] = JobStatus.RUNNING
        job["progress"] = 0.0
        
        # Execute code
        start_time = time.time()
        result = _execute_code(
            job["code"],
            job["context"],
            job["timeout"],
            progress_callback=lambda p: _update_progress(job_id, p)
        )
        end_time = time.time()
        
        # Store results
        job["result"] = result
        job["execution_time"] = end_time - start_time
        job["status"] = JobStatus.COMPLETE
        job["completed_at"] = datetime.now().isoformat()
        job["progress"] = 100.0
        
        logger.info(f"Job {job_id} completed in {job['execution_time']:.2f}s")
        
    except Exception as e:
        job["status"] = JobStatus.FAILED
        job["error"] = str(e)
        job["completed_at"] = datetime.now().isoformat()
        logger.error(f"Job {job_id} failed: {e}")
    
    finally:
        # Remove from running jobs
        async with scheduler_lock:
            if job_id in running_jobs:
                del running_jobs[job_id]


def _execute_code(code: str, context: Dict, timeout: int, progress_callback=None):
    """
    Execute code and return results.
    This is where you'd run k6, JMeter, Playwright, etc.
    """
    import subprocess
    import json
    
    # Example: Run k6 test
    # In real implementation, parse code to determine what to run
    
    # Simulate progress updates
    if progress_callback:
        for i in range(0, 100, 10):
            progress_callback(i)
            time.sleep(timeout / 10)  # Simulate work
    
    # Execute actual code
    # result = subprocess.run([...], capture_output=True, timeout=timeout)
    
    # For now, return mock result
    return {
        "status": "success",
        "metrics": {
            "requests": 180000,
            "avg_response_time": 160,
            "p95": 250
        }
    }


def _update_progress(job_id: str, progress: float):
    """Update job progress."""
    if job_id in jobs:
        jobs[job_id]["progress"] = progress


def _get_job_message(job: Dict, queue_position: Optional[int] = None) -> str:
    """Get human-readable job message."""
    if job["status"] == JobStatus.QUEUED:
        if queue_position:
            return f"Job queued (position: {queue_position})"
        return "Job queued, waiting to start"
    elif job["status"] == JobStatus.RUNNING:
        progress = job.get("progress", 0)
        return f"Job running ({progress:.1f}% complete)"
    elif job["status"] == JobStatus.COMPLETE:
        return "Job completed successfully"
    elif job["status"] == JobStatus.FAILED:
        return f"Job failed: {job.get('error', 'Unknown error')}"
    return "Unknown status"


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": AGENT_CONFIG.agent_id,
        "active_jobs": len(running_jobs),
        "queued_jobs": len(job_queue),
        "total_jobs": len(jobs),
        "max_concurrent": AGENT_CONFIG.max_concurrent_jobs,
        "available_slots": AGENT_CONFIG.max_concurrent_jobs - len(running_jobs)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_CONFIG.port)
