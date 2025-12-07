"""
CLI Client
API client for orchestrator with error handling and output formatting
"""

import json
from typing import Dict, Any, Optional
import httpx
from monitoring import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorClient:
    """Client for interacting with orchestrator API"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize orchestrator client
        
        Args:
            base_url: Base URL for API (defaults to settings)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.api_key = api_key or settings.API_KEY
        self.timeout = timeout
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
        
        logger.info("OrchestratorClient initialized", base_url=self.base_url)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Optional request body
            params: Optional query parameters
            
        Returns:
            Response data
            
        Raises:
            Exception on error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
            raise Exception(f"API error: {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def submit_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Submit a task
        
        Args:
            task_type: Type of task
            input_data: Task input data
            **kwargs: Additional task parameters
            
        Returns:
            Task response
        """
        task = {
            "type": task_type,
            "input": input_data,
            **kwargs
        }
        
        return self._make_request("POST", "/api/v1/tasks", data=task)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status
        """
        return self._make_request("GET", f"/api/v1/tasks/{task_id}")
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get task result
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result
        """
        return self._make_request("GET", f"/api/v1/tasks/{task_id}/result")
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List tasks
        
        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of tasks
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        return self._make_request("GET", "/api/v1/tasks", params=params)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            Cancellation confirmation
        """
        return self._make_request("POST", f"/api/v1/tasks/{task_id}/cancel")
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return self._make_request("GET", "/api/v1/health")


class OutputFormatter:
    """Format CLI output"""
    
    @staticmethod
    def format_json(data: Any) -> str:
        """Format data as JSON"""
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def format_table(data: list, headers: list) -> str:
        """Format data as table"""
        if not data:
            return "No data"
        
        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in data:
            for i, val in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(val)))
        
        # Create table
        lines = []
        
        # Header
        header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header_row)
        lines.append("-" * len(header_row))
        
        # Rows
        for row in data:
            row_str = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
            lines.append(row_str)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_task_status(task: Dict[str, Any]) -> str:
        """Format task status output"""
        lines = [
            f"Task ID: {task.get('task_id', 'N/A')}",
            f"Status: {task.get('status', 'N/A')}",
            f"Created: {task.get('created_at', 'N/A')}",
        ]
        
        if task.get('started_at'):
            lines.append(f"Started: {task.get('started_at')}")
        
        if task.get('completed_at'):
            lines.append(f"Completed: {task.get('completed_at')}")
        
        if task.get('error'):
            lines.append(f"Error: {task.get('error')}")
        
        if task.get('result'):
            lines.append(f"\nResult:\n{json.dumps(task.get('result'), indent=2)}")
        
        return "\n".join(lines)

