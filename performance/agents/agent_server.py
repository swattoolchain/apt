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
                'True': True,
                'False': False,
                'None': None,
            },
            **allowed_modules
        }
        
        exec_locals = request.context.copy()
        
        # Execute code with timeout
        start = time.time()
        
        try:
            # Use asyncio timeout for execution
            async def run_code():
                exec(request.code, exec_globals, exec_locals)
            
            await asyncio.wait_for(run_code(), timeout=request.timeout)
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail=f"Execution timeout after {request.timeout}s"
            )
        
        duration = time.time() - start
        
        # Extract result (code should set 'result' variable)
        result = exec_locals.get('result', {
            'duration': duration,
            'status': 'success',
            'message': 'No result variable set'
        })
        
        # Ensure result is a dict
        if not isinstance(result, dict):
            result = {'value': result, 'duration': duration}
        
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


@app.get("/")
async def root():
    """Root endpoint with agent information"""
    return {
        "agent": AGENT_NAME,
        "mode": AGENT_MODE,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "execute": "/execute",
            "metrics": "/metrics" if AGENT_MODE == 'serve' else None
        }
    }


if __name__ == "__main__":
    port = int(os.getenv('AGENT_PORT', 9090))
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  APT Remote Agent Server                                 ║
║  Name: {AGENT_NAME:<47} ║
║  Mode: {AGENT_MODE:<47} ║
║  Port: {port:<47} ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
