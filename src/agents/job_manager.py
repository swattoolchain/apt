"""
Async Job Manager for QPT Agent Server

Handles job-based asynchronous execution with filesystem storage.
"""

import json
import uuid
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import threading
from queue import PriorityQueue

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Job:
    """Represents an async execution job"""
    
    def __init__(self, job_id: str, code: str, context: Dict[str, Any], 
                 timeout: int = 300, priority: int = 5, tags: Dict[str, str] = None):
        self.job_id = job_id
        self.code = code
        self.context = context
        self.timeout = timeout
        self.priority = priority
        self.tags = tags or {}
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.duration = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "priority": self.priority,
            "tags": self.tags,
            "result": self.result,
            "error": self.error,
            "timeout": self.timeout
        }


class JobManager:
    """Manages async job execution and storage"""
    
    def __init__(self, jobs_dir: Path = None, max_concurrent: int = 1):
        """
        Initialize job manager.
        
        Args:
            jobs_dir: Directory to store job data
            max_concurrent: Maximum concurrent jobs (1 = FIFO queue)
        """
        self.jobs_dir = jobs_dir or Path.home() / "qpt_agent" / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent = max_concurrent
        self.jobs: Dict[str, Job] = {}
        self.job_queue = PriorityQueue()
        self.running_jobs = set()
        self.executor_thread = None
        self.running = False
        
        # Load existing jobs from filesystem
        self._load_existing_jobs()
        
        logger.info(f"JobManager initialized: jobs_dir={self.jobs_dir}, max_concurrent={max_concurrent}")
    
    def _load_existing_jobs(self):
        """Load existing jobs from filesystem"""
        try:
            for job_dir in self.jobs_dir.iterdir():
                if job_dir.is_dir():
                    status_file = job_dir / "status.json"
                    if status_file.exists():
                        with open(status_file) as f:
                            job_data = json.load(f)
                            job_id = job_data.get("job_id")
                            if job_id:
                                # Create minimal job object for tracking
                                job = Job(job_id, "", {})
                                job.status = JobStatus(job_data.get("status", "pending"))
                                job.created_at = job_data.get("created_at")
                                job.started_at = job_data.get("started_at")
                                job.completed_at = job_data.get("completed_at")
                                job.duration = job_data.get("duration")
                                self.jobs[job_id] = job
                                logger.debug(f"Loaded existing job: {job_id} (status={job.status})")
        except Exception as e:
            logger.warning(f"Failed to load existing jobs: {e}")
    
    def create_job(self, code: str, context: Dict[str, Any], 
                   timeout: int = 300, priority: int = 5, 
                   tags: Dict[str, str] = None) -> str:
        """
        Create a new job.
        
        Args:
            code: Python code to execute
            context: Execution context
            timeout: Execution timeout in seconds
            priority: Job priority (1-10, higher = more priority)
            tags: Optional tags for the job
            
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id, code, context, timeout, priority, tags)
        
        # Create job directory
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)
        
        # Save job definition
        with open(job_dir / "job.json", 'w') as f:
            json.dump({
                "job_id": job_id,
                "code": code,
                "context": context,
                "timeout": timeout,
                "priority": priority,
                "tags": tags,
                "created_at": job.created_at
            }, f, indent=2)
        
        # Save initial status
        self._save_job_status(job)
        
        # Add to queue (negative priority for max-heap behavior)
        self.jobs[job_id] = job
        self.job_queue.put((-priority, time.time(), job_id))
        
        logger.info(f"Created job: {job_id} (priority={priority})")
        
        # Start executor if not running
        if not self.running:
            self.start()
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and result"""
        job = self.jobs.get(job_id)
        if not job:
            # Try to load from filesystem
            job_dir = self.jobs_dir / job_id
            if job_dir.exists():
                status_file = job_dir / "status.json"
                if status_file.exists():
                    with open(status_file) as f:
                        return json.load(f)
            return None
        
        return job.to_dict()
    
    def get_job_logs(self, job_id: str) -> Optional[str]:
        """Get job execution logs"""
        log_file = self.jobs_dir / job_id / "logs" / "execution.log"
        if log_file.exists():
            return log_file.read_text()
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow().isoformat()
            self._save_job_status(job)
            logger.info(f"Cancelled job: {job_id}")
            return True
        
        return False
    
    def delete_job(self, job_id: str, preserve_logs: bool = True) -> bool:
        """Delete a job and its data"""
        job_dir = self.jobs_dir / job_id
        if not job_dir.exists():
            return False
        
        try:
            if preserve_logs:
                # Keep logs, delete everything else
                for item in job_dir.iterdir():
                    if item.name != "logs":
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            import shutil
                            shutil.rmtree(item)
            else:
                # Delete everything
                import shutil
                shutil.rmtree(job_dir)
            
            # Remove from memory
            if job_id in self.jobs:
                del self.jobs[job_id]
            
            logger.info(f"Deleted job: {job_id} (preserve_logs={preserve_logs})")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status"""
        jobs = []
        for job in self.jobs.values():
            if status is None or job.status == status:
                jobs.append(job.to_dict())
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]
    
    def _save_job_status(self, job: Job):
        """Save job status to filesystem"""
        status_file = self.jobs_dir / job.job_id / "status.json"
        with open(status_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)
    
    def _save_job_result(self, job: Job):
        """Save job result to filesystem"""
        result_file = self.jobs_dir / job.job_id / "result.json"
        with open(result_file, 'w') as f:
            json.dump({
                "job_id": job.job_id,
                "status": job.status.value,
                "result": job.result,
                "error": job.error,
                "duration": job.duration,
                "completed_at": job.completed_at
            }, f, indent=2)
    
    async def _execute_job(self, job: Job):
        """Execute a single job"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow().isoformat()
        self._save_job_status(job)
        
        log_file = self.jobs_dir / job.job_id / "logs" / "execution.log"
        
        try:
            logger.info(f"Executing job: {job.job_id}")
            
            # Prepare execution environment (matching AgentServer restricted env)
            allowed_modules = {
                'time': __import__('time'),
                'json': __import__('json'),
                'requests': __import__('requests'),
                'datetime': __import__('datetime'),
                'math': __import__('math'),
                'subprocess': __import__('subprocess'),
                'os': __import__('os'),
                'shutil': __import__('shutil'),
                'platform': __import__('platform'),
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
                },
                **allowed_modules
            }
            
            exec_locals = job.context.copy()
            exec_locals['context'] = job.context
            exec_locals['result'] = None
            
            # Execute code with timeout
            start_time = time.time()
            
            # Run in thread pool to support timeout
            loop = asyncio.get_event_loop()
            
            def sync_exec():
                exec(job.code, exec_globals, exec_locals)
                return exec_locals.get('result')
            
            result = await asyncio.wait_for(
                loop.run_in_executor(None, sync_exec),
                timeout=job.timeout
            )
            
            duration = time.time() - start_time
            
            # Get result
            result = exec_globals.get("result") or exec_locals.get("result")
            
            job.status = JobStatus.COMPLETED
            job.result = result
            job.duration = duration
            job.completed_at = datetime.utcnow().isoformat()
            
            # Save logs
            with open(log_file, 'w') as f:
                f.write(f"Job {job.job_id} completed successfully\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(f"Result: {result}\n")
            
            logger.info(f"Job completed: {job.job_id} (duration={duration:.2f}s)")
            
        except asyncio.TimeoutError:
            job.status = JobStatus.TIMEOUT
            job.error = f"Job exceeded timeout of {job.timeout}s"
            job.completed_at = datetime.utcnow().isoformat()
            
            with open(log_file, 'w') as f:
                f.write(f"Job {job.job_id} timed out after {job.timeout}s\n")
            
            logger.warning(f"Job timeout: {job.job_id}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow().isoformat()
            
            with open(log_file, 'w') as f:
                f.write(f"Job {job.job_id} failed with error:\n")
                f.write(f"{str(e)}\n")
                import traceback
                f.write(traceback.format_exc())
            
            logger.error(f"Job failed: {job.job_id} - {e}")
        
        finally:
            self._save_job_status(job)
            self._save_job_result(job)
            self.running_jobs.discard(job.job_id)
    
    async def _executor_loop(self):
        """Main executor loop"""
        logger.info("Job executor started")
        
        while self.running:
            try:
                # Check if we can run more jobs
                if len(self.running_jobs) < self.max_concurrent and not self.job_queue.empty():
                    # Get next job from queue
                    _, _, job_id = self.job_queue.get_nowait()
                    
                    job = self.jobs.get(job_id)
                    if job and job.status == JobStatus.PENDING:
                        self.running_jobs.add(job_id)
                        # Execute job in background
                        asyncio.create_task(self._execute_job(job))
                
                # Small sleep to avoid busy loop
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Executor loop error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Job executor stopped")
    
    def start(self):
        """Start the job executor"""
        if not self.running:
            self.running = True
            # Start executor in background
            asyncio.create_task(self._executor_loop())
            logger.info("Job executor started")
    
    def stop(self):
        """Stop the job executor"""
        self.running = False
        logger.info("Job executor stopping...")
