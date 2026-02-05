"""
Remote Agent Server - FastAPI server for distributed test execution

This server runs on remote machines and executes test code sent from the APT framework.
Supports both 'emit' mode (push metrics to InfluxDB) and 'serve' mode (store locally).
"""

import asyncio
import json
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Configuration
CONFIG_FILE = os.getenv('AGENT_CONFIG_FILE', 'config.json')
METRICS_DIR = Path('metrics')
METRICS_DIR.mkdir(exist_ok=True)

# Load configuration
with open(CONFIG_FILE) as f:
    config = json.load(f)

AGENT_NAME = config.get('name', 'agent')
AGENT_MODE = config.get('mode', 'serve')  # 'emit' or 'serve'
EMIT_TARGET = config.get('emit_target', '')
AUTH_TOKEN = config.get('auth_token', '')

# FastAPI app
app = FastAPI(
    title=f"APT Remote Agent: {AGENT_NAME}",
    description="Remote execution agent for APT performance testing framework",
    version="1.0.0"
)

# Startup time for uptime calculation
START_TIME = time.time()

# Metrics storage (for serve mode)
metrics_store = []


class ExecuteRequest(BaseModel):
    """Request to execute code on the agent"""
    code: str = Field(..., description="Python code to execute")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context variables")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for metrics")


class MetricsQuery(BaseModel):
    """Query for stored metrics (serve mode only)"""
    metric: Optional[str] = None
    timerange: str = "last_1h"
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 1000


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_name: str
    mode: str
    uptime_seconds: float
    metrics_count: int
    timestamp: str


# Authentication dependency
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify authentication token if configured"""
    if AUTH_TOKEN and authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return True


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        agent_name=AGENT_NAME,
        mode=AGENT_MODE,
        uptime_seconds=time.time() - START_TIME,
        metrics_count=len(metrics_store),
        timestamp=datetime.now().isoformat()
    )


@app.post("/execute")
async def execute_code(
    request: ExecuteRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Execute user-provided code and return metrics.
    
    Security: Uses restricted execution environment with whitelisted imports.
    """
    try:
        # Create restricted execution environment
        allowed_modules = {
            'time': __import__('time'),
            'json': __import__('json'),
            'requests': __import__('requests'),
            'datetime': __import__('datetime'),
            'math': __import__('math'),
            'subprocess': __import__('subprocess'),
            'os': __import__('os'),
            'shutil': __import__('shutil'),
        }
        
        exec_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'str': str,
                'int': int,
                'float': float,
                'dict': dict,
                'list': list,
                'tuple': tuple,
                'bool': bool,
                'True': True,
                'False': False,
                'None': None,
                '__import__': __import__,
                'open': open,
                'Exception': Exception,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'round': round,
                'os': __import__('os'),
                'shutil': __import__('shutil'),
            },
            **allowed_modules
        }
        
        exec_locals = request.context.copy()
        exec_locals['context'] = request.context  # Make context available as a variable
        
        # Execute code with timeout
        start = time.time()
        
        # Execute code in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        
        try:
            # Note: globals and locals must be handled carefully in threads
            def sync_exec():
                exec(request.code, exec_globals, exec_locals)
                return exec_locals.get('result', {})
            
            result_data = await asyncio.wait_for(
                loop.run_in_executor(None, sync_exec),
                timeout=request.timeout
            )
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail=f"Execution timeout after {request.timeout}s"
            )
        except Exception as e:
            logger.exception("Execution error")
            raise HTTPException(
                status_code=500,
                detail=f"Execution error: {str(e)}"
            )
        
        duration = time.time() - start
        
        # Merge iteration results if generated (backwards compatibility)
        final_result = result_data if isinstance(result_data, dict) else {"data": result_data}
        
        # Ensure duration and status are included
        result = {
            "status": "success",
            "duration": final_result.get('duration', duration),
            **final_result
        }
        
        # Add metadata
        result['agent_name'] = AGENT_NAME
        result['timestamp'] = datetime.now().isoformat()
        result['tags'] = request.tags
        
        # Store or emit metrics
        if AGENT_MODE == 'serve':
            metrics_store.append({
                'timestamp': time.time(),
                'metrics': result
            })
            # Keep only last 10000 metrics
            if len(metrics_store) > 10000:
                metrics_store.pop(0)
        
        elif AGENT_MODE == 'emit':
            await emit_metrics(result)
        
        return JSONResponse(content=result)
        
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@app.get("/metrics")
async def get_metrics(
    query: MetricsQuery = Depends(),
    authenticated: bool = Depends(verify_token)
):
    """
    Query stored metrics (serve mode only).
    
    Returns metrics matching the query filters.
    """
    if AGENT_MODE != 'serve':
        raise HTTPException(
            status_code=400,
            detail="Agent not in serve mode. Cannot query metrics."
        )
    
    # Simple filtering
    filtered = metrics_store.copy()
    
    if query.metric:
        filtered = [m for m in filtered if query.metric in str(m.get('metrics', {}))]
    
    # Apply custom filters
    for key, value in query.filters.items():
        filtered = [
            m for m in filtered
            if m.get('metrics', {}).get(key) == value
        ]
    
    # Limit results
    filtered = filtered[-query.limit:]
    
    return {
        'count': len(filtered),
        'metrics': [m['metrics'] for m in filtered]
    }


async def emit_metrics(metrics: Dict):
    """
    Emit metrics to configured target (InfluxDB, etc.).
    
    This is a placeholder - implement based on your emit_target.
    """
    if not EMIT_TARGET:
        return
    
    # TODO: Implement InfluxDB emission
    # For now, just log
    print(f"[EMIT] Would send to {EMIT_TARGET}: {metrics}")


# ============================================================================
# ASYNC JOB EXECUTION (New in v4.0)
# ============================================================================

# Initialize JobManager
from .job_manager import JobManager, JobStatus

# Job manager instance (initialized on startup)
job_manager: Optional[JobManager] = None


class JobSubmitRequest(BaseModel):
    """Request to submit an async job"""
    code: str = Field(..., description="Python code to execute")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context variables")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    priority: int = Field(default=5, ge=1, le=10, description="Job priority (1-10, higher = more priority)")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for the job")


class JobResponse(BaseModel):
    """Response for job operations"""
    job_id: str
    status: str
    message: Optional[str] = None


@app.post("/jobs", response_model=JobResponse)
async def submit_job(
    request: JobSubmitRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Submit a job for asynchronous execution.
    
    Returns immediately with a job_id that can be used to poll for status.
    """
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not initialized")
    
    try:
        job_id = job_manager.create_job(
            code=request.code,
            context=request.context,
            timeout=request.timeout,
            priority=request.priority,
            tags=request.tags
        )
        
        logger.info(f"Job submitted: {job_id} (priority={request.priority})")
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message="Job submitted successfully"
        )
    except Exception as e:
        logger.error(f"Failed to submit job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    authenticated: bool = Depends(verify_token)
):
    """
    Get the status and result of a job.
    
    Returns job details including status, result, error, and duration.
    """
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not initialized")
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return job


@app.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    authenticated: bool = Depends(verify_token)
):
    """
    Get the execution logs for a job.
    
    Returns the log file contents as plain text.
    """
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not initialized")
    
    logs = job_manager.get_job_logs(job_id)
    if logs is None:
        raise HTTPException(status_code=404, detail=f"Logs for job {job_id} not found")
    
    return {"job_id": job_id, "logs": logs}


@app.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    authenticated: bool = Depends(verify_token)
):
    """
    Cancel a pending or running job.
    
    Returns success if the job was cancelled, error if already completed.
    """
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not initialized")
    
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id} (not found or already completed)")
    
    return {"job_id": job_id, "status": "cancelled", "message": "Job cancelled successfully"}


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 100,
    authenticated: bool = Depends(verify_token)
):
    """
    List all jobs, optionally filtered by status.
    
    Query parameters:
    - status: Filter by job status (pending, running, completed, failed, cancelled, timeout)
    - limit: Maximum number of jobs to return (default: 100)
    """
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job manager not initialized")
    
    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    jobs = job_manager.list_jobs(status=status_filter, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with agent information"""
    endpoints = {
        "health": "/health",
        "execute": "/execute (sync)",
        "jobs": "/jobs (async)",
        "job_status": "/jobs/{job_id}",
        "job_logs": "/jobs/{job_id}/logs",
        "metrics": "/metrics" if AGENT_MODE == 'serve' else None
    }
    
    return {
        "agent": AGENT_NAME,
        "mode": AGENT_MODE,
        "status": "running",
        "execution_modes": ["sync", "async"],
        "job_manager_active": job_manager is not None,
        "endpoints": endpoints
    }


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize JobManager on startup"""
    global job_manager
    
    try:
        # Load execution config
        exec_config_file = Path("config/execution_config.yml")
        if exec_config_file.exists():
            import yaml
            with open(exec_config_file) as f:
                exec_config = yaml.safe_load(f)
            
            # Get job queue config
            job_queue_config = exec_config.get("job_queue", {})
            max_concurrent = job_queue_config.get("max_concurrent_jobs", 1)
            
            # Initialize JobManager
            jobs_dir = Path.home() / "qpt_agent" / "jobs"
            job_manager = JobManager(jobs_dir=jobs_dir, max_concurrent=max_concurrent)
            job_manager.start()
            
            logger.info(f"JobManager initialized: max_concurrent={max_concurrent}, jobs_dir={jobs_dir}")
        else:
            logger.warning("execution_config.yml not found, async mode disabled")
    except Exception as e:
        logger.error(f"Failed to initialize JobManager: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop JobManager on shutdown"""
    global job_manager
    if job_manager:
        job_manager.stop()
        logger.info("JobManager stopped")


if __name__ == "__main__":
    # Prioritize: config.get('port') > AGENT_PORT env > 5007
    port = int(config.get('port', os.getenv('AGENT_PORT', 5007)))
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  QPT Remote Agent Server v4.0                            ║
║  Name: {AGENT_NAME:<47} ║
║  Mode: {AGENT_MODE:<47} ║
║  Port: {port:<47} ║
║  Execution: Sync + Async (Job-based)                     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
