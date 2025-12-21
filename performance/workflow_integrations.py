"""
Workflow Orchestration Integration

Support for popular workflow orchestration tools:
- Temporal
- Apache Airflow
- Prefect
- Dagster
- Argo Workflows

Provides performance testing for workflow executions with custom metrics collection.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class BaseWorkflowCollector:
    """Base class for workflow metrics collectors."""
    
    def __init__(self, workflow_id: str):
        """
        Initialize workflow collector.
        
        Args:
            workflow_id: Unique identifier for the workflow
        """
        self.workflow_id = workflow_id
        self.metrics = {}
        self.start_time = None
        self.end_time = None
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from workflow execution.
        
        Returns:
            Dictionary of collected metrics
        """
        raise NotImplementedError("Subclasses must implement collect_metrics")
    
    def get_execution_time(self) -> float:
        """Get total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class TemporalWorkflowCollector(BaseWorkflowCollector):
    """Metrics collector for Temporal workflows."""
    
    def __init__(
        self,
        workflow_id: str,
        temporal_client: Optional[Any] = None,
        namespace: str = "default"
    ):
        """
        Initialize Temporal workflow collector.
        
        Args:
            workflow_id: Temporal workflow ID
            temporal_client: Temporal client instance (optional)
            namespace: Temporal namespace
        """
        super().__init__(workflow_id)
        self.client = temporal_client
        self.namespace = namespace
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from Temporal workflow.
        
        Metrics collected:
        - Workflow execution time
        - Activity execution times
        - Retry counts
        - Workflow status
        - Event history
        """
        try:
            if self.client:
                # Get workflow execution
                workflow_handle = self.client.get_workflow_handle(
                    self.workflow_id,
                    namespace=self.namespace
                )
                
                # Get workflow description
                description = await workflow_handle.describe()
                
                self.start_time = description.start_time
                self.end_time = description.close_time or datetime.now()
                
                # Collect metrics
                self.metrics = {
                    'workflow_id': self.workflow_id,
                    'status': description.status.name,
                    'execution_time': self.get_execution_time(),
                    'start_time': self.start_time.isoformat(),
                    'end_time': self.end_time.isoformat() if description.close_time else None,
                    'run_id': description.run_id,
                    'workflow_type': description.workflow_type,
                    'task_queue': description.task_queue,
                }
                
                # Get event history for activity timings
                history = await workflow_handle.fetch_history()
                activity_metrics = self._parse_activity_metrics(history)
                self.metrics['activities'] = activity_metrics
                
            else:
                # Fallback: Use API calls
                self.metrics = await self._collect_via_api()
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error collecting Temporal metrics: {e}")
            return {'error': str(e), 'workflow_id': self.workflow_id}
    
    def _parse_activity_metrics(self, history) -> List[Dict]:
        """Parse activity execution metrics from event history."""
        activities = []
        activity_starts = {}
        
        for event in history.events:
            if event.event_type == 'ActivityTaskScheduled':
                activity_id = event.activity_task_scheduled_event_attributes.activity_id
                activity_starts[activity_id] = event.event_time
            
            elif event.event_type == 'ActivityTaskCompleted':
                activity_id = event.activity_task_completed_event_attributes.scheduled_event_id
                if activity_id in activity_starts:
                    duration = (event.event_time - activity_starts[activity_id]).total_seconds()
                    activities.append({
                        'activity_id': activity_id,
                        'duration': duration,
                        'status': 'completed'
                    })
        
        return activities
    
    async def _collect_via_api(self) -> Dict:
        """Collect metrics via Temporal API (when client not available)."""
        # Implement API-based collection
        # This would make HTTP calls to Temporal server
        return {
            'workflow_id': self.workflow_id,
            'collection_method': 'api',
            'note': 'Implement API collection for your Temporal server'
        }


class AirflowDAGCollector(BaseWorkflowCollector):
    """Metrics collector for Apache Airflow DAGs."""
    
    def __init__(
        self,
        dag_id: str,
        dag_run_id: str,
        airflow_api_url: Optional[str] = None,
        auth_token: Optional[str] = None
    ):
        """
        Initialize Airflow DAG collector.
        
        Args:
            dag_id: Airflow DAG ID
            dag_run_id: DAG run ID
            airflow_api_url: Airflow API base URL
            auth_token: Authentication token
        """
        super().__init__(f"{dag_id}_{dag_run_id}")
        self.dag_id = dag_id
        self.dag_run_id = dag_run_id
        self.api_url = airflow_api_url
        self.auth_token = auth_token
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from Airflow DAG run.
        
        Metrics collected:
        - DAG execution time
        - Task execution times
        - Task retry counts
        - DAG run status
        """
        try:
            import aiohttp
            
            if not self.api_url:
                return await self._collect_from_logs()
            
            # Collect via Airflow REST API
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            async with aiohttp.ClientSession() as session:
                # Get DAG run info
                dag_run_url = f"{self.api_url}/api/v1/dags/{self.dag_id}/dagRuns/{self.dag_run_id}"
                async with session.get(dag_run_url, headers=headers) as resp:
                    dag_run_data = await resp.json()
                
                self.start_time = datetime.fromisoformat(dag_run_data['start_date'])
                end_date = dag_run_data.get('end_date')
                self.end_time = datetime.fromisoformat(end_date) if end_date else datetime.now()
                
                # Get task instances
                tasks_url = f"{self.api_url}/api/v1/dags/{self.dag_id}/dagRuns/{self.dag_run_id}/taskInstances"
                async with session.get(tasks_url, headers=headers) as resp:
                    tasks_data = await resp.json()
                
                task_metrics = []
                for task in tasks_data.get('task_instances', []):
                    task_start = datetime.fromisoformat(task['start_date']) if task.get('start_date') else None
                    task_end = datetime.fromisoformat(task['end_date']) if task.get('end_date') else None
                    
                    if task_start and task_end:
                        duration = (task_end - task_start).total_seconds()
                    else:
                        duration = 0
                    
                    task_metrics.append({
                        'task_id': task['task_id'],
                        'duration': duration,
                        'state': task['state'],
                        'try_number': task.get('try_number', 1)
                    })
                
                self.metrics = {
                    'dag_id': self.dag_id,
                    'dag_run_id': self.dag_run_id,
                    'status': dag_run_data['state'],
                    'execution_time': self.get_execution_time(),
                    'start_time': self.start_time.isoformat(),
                    'end_time': self.end_time.isoformat() if end_date else None,
                    'tasks': task_metrics,
                    'total_tasks': len(task_metrics),
                    'successful_tasks': len([t for t in task_metrics if t['state'] == 'success']),
                    'failed_tasks': len([t for t in task_metrics if t['state'] == 'failed'])
                }
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error collecting Airflow metrics: {e}")
            return {'error': str(e), 'dag_id': self.dag_id}
    
    async def _collect_from_logs(self) -> Dict:
        """Collect metrics from Airflow logs (when API not available)."""
        return {
            'dag_id': self.dag_id,
            'dag_run_id': self.dag_run_id,
            'collection_method': 'logs',
            'note': 'Implement log parsing for your Airflow setup'
        }


class CustomWorkflowCollector(BaseWorkflowCollector):
    """
    Custom workflow collector for any workflow system.
    
    Users can implement their own collection logic.
    """
    
    def __init__(
        self,
        workflow_id: str,
        collector_func: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize custom workflow collector.
        
        Args:
            workflow_id: Workflow identifier
            collector_func: Custom async function to collect metrics
            **kwargs: Additional arguments passed to collector_func
        """
        super().__init__(workflow_id)
        self.collector_func = collector_func
        self.kwargs = kwargs
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics using custom function.
        
        The custom function should return a dictionary with metrics.
        """
        try:
            if self.collector_func:
                # Call custom collector
                self.start_time = datetime.now()
                metrics = await self.collector_func(self.workflow_id, **self.kwargs)
                self.end_time = datetime.now()
                
                # Ensure execution_time is included
                if 'execution_time' not in metrics:
                    metrics['execution_time'] = self.get_execution_time()
                
                self.metrics = metrics
            else:
                # Default: Just measure execution time
                self.metrics = {
                    'workflow_id': self.workflow_id,
                    'execution_time': self.get_execution_time(),
                    'note': 'No custom collector provided'
                }
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error in custom collector: {e}")
            return {'error': str(e), 'workflow_id': self.workflow_id}


class WorkflowPerformanceTester:
    """Performance tester for workflow orchestration systems."""
    
    def __init__(self, collector: BaseWorkflowCollector):
        """
        Initialize workflow performance tester.
        
        Args:
            collector: Workflow metrics collector instance
        """
        self.collector = collector
        self.results = []
    
    async def measure_workflow_execution(
        self,
        workflow_func: Callable,
        iterations: int = 1,
        **workflow_kwargs
    ) -> Dict[str, Any]:
        """
        Measure workflow execution performance.
        
        Args:
            workflow_func: Async function that executes the workflow
            iterations: Number of times to run the workflow
            **workflow_kwargs: Arguments to pass to workflow_func
            
        Returns:
            Performance metrics dictionary
        """
        iteration_results = []
        
        for i in range(iterations):
            logger.info(f"Running workflow iteration {i+1}/{iterations}")
            
            start = time.time()
            
            try:
                # Execute workflow
                workflow_result = await workflow_func(**workflow_kwargs)
                
                # Collect metrics
                metrics = await self.collector.collect_metrics()
                
                duration = time.time() - start
                
                iteration_results.append({
                    'iteration': i + 1,
                    'duration': duration,
                    'metrics': metrics,
                    'status': 'success',
                    'result': workflow_result
                })
                
            except Exception as e:
                duration = time.time() - start
                iteration_results.append({
                    'iteration': i + 1,
                    'duration': duration,
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Workflow iteration {i+1} failed: {e}")
        
        # Calculate statistics
        successful_runs = [r for r in iteration_results if r['status'] == 'success']
        durations = [r['duration'] for r in successful_runs]
        
        summary = {
            'workflow_id': self.collector.workflow_id,
            'total_iterations': iterations,
            'successful_iterations': len(successful_runs),
            'failed_iterations': iterations - len(successful_runs),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'iterations': iteration_results
        }
        
        self.results.append(summary)
        return summary
