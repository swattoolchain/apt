"""
APT Web UI - Backend API

FastAPI backend for the APT Web UI providing REST API and WebSocket endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio
import json
import uuid

# Import APT framework components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from performance.agents import AgentRegistry, AgentProvisioner, AgentDeployer, DeploymentMethod, DeploymentTarget
from performance.unified_yaml_loader import UnifiedYAMLTestRunner

# FastAPI app
app = FastAPI(
    title="APT Web UI API",
    description="Backend API for APT Performance Testing Framework",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
tests_db = {}
agents_db = {}
executions_db = {}
results_db = {}

# WebSocket connections
active_connections: List[WebSocket] = []


# ============================================================================
# Models
# ============================================================================

class TestDefinition(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    test_type: str  # k6, jmeter, workflow, hybrid
    config: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AgentDefinition(BaseModel):
    id: Optional[str] = None
    name: str
    deployment_type: str  # docker, cron, systemd, shell
    mode: str  # emit, serve
    endpoint: Optional[str] = None
    status: Optional[str] = "unknown"
    created_at: Optional[datetime] = None


class TestExecution(BaseModel):
    id: Optional[str] = None
    test_id: str
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None


# ============================================================================
# WebSocket Manager
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# ============================================================================
# API Endpoints - Tests
# ============================================================================

@app.get("/api/tests", response_model=List[TestDefinition])
async def list_tests():
    """List all test definitions"""
    return list(tests_db.values())


@app.post("/api/tests", response_model=TestDefinition)
async def create_test(test: TestDefinition):
    """Create a new test definition"""
    test.id = str(uuid.uuid4())
    test.created_at = datetime.now()
    test.updated_at = datetime.now()
    tests_db[test.id] = test
    
    await manager.broadcast({
        "type": "test_created",
        "data": test.dict()
    })
    
    return test


@app.get("/api/tests/{test_id}", response_model=TestDefinition)
async def get_test(test_id: str):
    """Get a specific test definition"""
    if test_id not in tests_db:
        raise HTTPException(status_code=404, detail="Test not found")
    return tests_db[test_id]


@app.put("/api/tests/{test_id}", response_model=TestDefinition)
async def update_test(test_id: str, test: TestDefinition):
    """Update a test definition"""
    if test_id not in tests_db:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test.id = test_id
    test.updated_at = datetime.now()
    tests_db[test_id] = test
    
    await manager.broadcast({
        "type": "test_updated",
        "data": test.dict()
    })
    
    return test


@app.delete("/api/tests/{test_id}")
async def delete_test(test_id: str):
    """Delete a test definition"""
    if test_id not in tests_db:
        raise HTTPException(status_code=404, detail="Test not found")
    
    del tests_db[test_id]
    
    await manager.broadcast({
        "type": "test_deleted",
        "data": {"id": test_id}
    })
    
    return {"message": "Test deleted"}


# ============================================================================
# API Endpoints - Agents
# ============================================================================

@app.get("/api/agents", response_model=List[AgentDefinition])
async def list_agents():
    """List all agents"""
    return list(agents_db.values())


@app.post("/api/agents", response_model=AgentDefinition)
async def create_agent(agent: AgentDefinition):
    """Create a new agent"""
    agent.id = str(uuid.uuid4())
    agent.created_at = datetime.now()
    agent.status = "created"
    agents_db[agent.id] = agent
    
    # Generate agent package
    provisioner = AgentProvisioner()
    method_map = {
        'docker': DeploymentMethod.DOCKER,
        'cron': DeploymentMethod.CRON,
        'systemd': DeploymentMethod.SYSTEMD,
        'shell': DeploymentMethod.SHELL
    }
    
    config = {
        'mode': agent.mode,
        'emit_target': '',
        'auth_token': str(uuid.uuid4())
    }
    
    package_dir = provisioner.create_agent(
        agent.name,
        method_map[agent.deployment_type],
        config
    )
    
    await manager.broadcast({
        "type": "agent_created",
        "data": agent.dict()
    })
    
    return agent


@app.post("/api/agents/{agent_id}/deploy")
async def deploy_agent(agent_id: str, target: str, ssh_key: Optional[str] = None):
    """Deploy an agent to a remote server"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Deploy agent
    deployer = AgentDeployer()
    deployment_target = DeploymentTarget.from_string(target, ssh_key)
    
    method_map = {
        'docker': DeploymentMethod.DOCKER,
        'cron': DeploymentMethod.CRON,
        'systemd': DeploymentMethod.SYSTEMD,
        'shell': DeploymentMethod.SHELL
    }
    
    package_dir = Path.home() / ".apt" / "agents" / agent.name
    
    success = await deployer.deploy(
        agent.name,
        package_dir,
        deployment_target,
        method_map[agent.deployment_type],
        "/opt/apt-agent"
    )
    
    if success:
        agent.status = "deployed"
        agent.endpoint = f"http://{target.split('@')[1]}:9090"
        agents_db[agent_id] = agent
        
        await manager.broadcast({
            "type": "agent_deployed",
            "data": agent.dict()
        })
        
        return {"message": "Agent deployed successfully", "agent": agent}
    else:
        raise HTTPException(status_code=500, detail="Deployment failed")


@app.get("/api/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get agent health status"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents_db[agent_id]
    
    # Check health
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{agent.endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
    except:
        return {"status": "unhealthy"}


# ============================================================================
# API Endpoints - Execution
# ============================================================================

@app.post("/api/executions", response_model=TestExecution)
async def execute_test(test_id: str):
    """Execute a test"""
    if test_id not in tests_db:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test = tests_db[test_id]
    
    execution = TestExecution(
        id=str(uuid.uuid4()),
        test_id=test_id,
        status="pending",
        started_at=datetime.now()
    )
    
    executions_db[execution.id] = execution
    
    # Run test asynchronously
    asyncio.create_task(run_test_async(execution.id, test))
    
    await manager.broadcast({
        "type": "execution_started",
        "data": execution.dict()
    })
    
    return execution


@app.get("/api/executions/{execution_id}", response_model=TestExecution)
async def get_execution(execution_id: str):
    """Get execution status"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions_db[execution_id]


@app.get("/api/executions", response_model=List[TestExecution])
async def list_executions():
    """List all executions"""
    return list(executions_db.values())


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Helper Functions
# ============================================================================

async def run_test_async(execution_id: str, test: TestDefinition):
    """Run test asynchronously"""
    execution = executions_db[execution_id]
    execution.status = "running"
    
    await manager.broadcast({
        "type": "execution_status",
        "data": {"id": execution_id, "status": "running"}
    })
    
    try:
        # Generate YAML file
        yaml_file = Path(f"/tmp/test_{execution_id}.yml")
        yaml_content = generate_yaml_from_config(test.config)
        yaml_file.write_text(yaml_content)
        
        # Run test
        runner = UnifiedYAMLTestRunner(yaml_file)
        results = await runner.run_all_tests()
        
        execution.status = "completed"
        execution.completed_at = datetime.now()
        execution.results = results
        
        await manager.broadcast({
            "type": "execution_completed",
            "data": execution.dict()
        })
        
    except Exception as e:
        execution.status = "failed"
        execution.completed_at = datetime.now()
        execution.results = {"error": str(e)}
        
        await manager.broadcast({
            "type": "execution_failed",
            "data": execution.dict()
        })
    
    executions_db[execution_id] = execution


def generate_yaml_from_config(config: Dict[str, Any]) -> str:
    """Generate YAML from test configuration"""
    import yaml
    return yaml.dump(config, default_flow_style=False)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "APT Web UI API",
        "version": "1.0.0",
        "endpoints": {
            "tests": "/api/tests",
            "agents": "/api/agents",
            "executions": "/api/executions",
            "websocket": "/ws"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
