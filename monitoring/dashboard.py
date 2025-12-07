"""
Monitoring Dashboard
Real-time monitoring dashboard for orchestrator system
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from monitoring import get_logger
from monitoring.metrics import get_metrics_collector
from monitoring.health import SystemHealthChecker, HealthMonitor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

logger = get_logger(__name__)


class MonitoringDashboard:
    """
    Basic monitoring dashboard
    
    Provides:
    - Real-time metrics display
    - Health status monitoring
    - System overview
    """
    
    def __init__(
        self,
        health_checker: Optional[SystemHealthChecker] = None
    ):
        """
        Initialize monitoring dashboard
        
        Args:
            health_checker: Optional SystemHealthChecker instance
        """
        self.health_checker = health_checker
        self.metrics_collector = get_metrics_collector()
        logger.info("MonitoringDashboard initialized")
    
    def get_dashboard_html(self) -> str:
        """Get dashboard HTML page"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Orchestrator AI Agent - Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #666; }
        .metric-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-healthy { background: #10b981; color: white; }
        .status-degraded { background: #f59e0b; color: white; }
        .status-unhealthy { background: #ef4444; color: white; }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 20px;
        }
        .refresh-btn:hover { background: #5568d3; }
        .timestamp {
            color: #999;
            font-size: 0.9em;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Orchestrator AI Agent</h1>
            <p>Real-time Monitoring Dashboard</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>System Health</h2>
                <div id="health-status">Loading...</div>
                <div id="health-checks">Loading...</div>
            </div>
            
            <div class="card">
                <h2>Task Metrics</h2>
                <div id="task-metrics">Loading...</div>
            </div>
            
            <div class="card">
                <h2>Workflow Metrics</h2>
                <div id="workflow-metrics">Loading...</div>
            </div>
            
            <div class="card">
                <h2>Agent Metrics</h2>
                <div id="agent-metrics">Loading...</div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh</button>
        <div class="timestamp" id="last-update">Last updated: -</div>
    </div>
    
    <script>
        async function loadDashboard() {
            try {
                // Load health status
                const healthRes = await fetch('/api/v1/health');
                const health = await healthRes.json();
                updateHealthStatus(health);
                
                // Load metrics (would need metrics endpoint)
                updateMetrics();
                
                document.getElementById('last-update').textContent = 
                    'Last updated: ' + new Date().toLocaleString();
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }
        
        function updateHealthStatus(health) {
            const statusDiv = document.getElementById('health-status');
            const statusClass = 'status-' + health.status.toLowerCase();
            statusDiv.innerHTML = `
                <div class="metric">
                    <span class="metric-label">Overall Status</span>
                    <span class="metric-value">
                        <span class="status-badge ${statusClass}">${health.status.toUpperCase()}</span>
                    </span>
                </div>
            `;
            
            const checksDiv = document.getElementById('health-checks');
            let checksHtml = '';
            for (const [name, check] of Object.entries(health.checks || {})) {
                const checkClass = 'status-' + check.status.toLowerCase();
                checksHtml += `
                    <div class="metric">
                        <span class="metric-label">${name}</span>
                        <span class="status-badge ${checkClass}">${check.status}</span>
                    </div>
                `;
            }
            checksDiv.innerHTML = checksHtml || '<p>No health checks available</p>';
        }
        
        function updateMetrics() {
            // Placeholder for metrics - would fetch from /metrics endpoint
            document.getElementById('task-metrics').innerHTML = 
                '<p>Metrics endpoint coming soon</p>';
            document.getElementById('workflow-metrics').innerHTML = 
                '<p>Metrics endpoint coming soon</p>';
            document.getElementById('agent-metrics').innerHTML = 
                '<p>Metrics endpoint coming soon</p>';
        }
        
        // Load dashboard on page load
        loadDashboard();
        
        // Auto-refresh every 5 seconds
        setInterval(loadDashboard, 5000);
    </script>
</body>
</html>
        """
    
    def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system overview data
        
        Returns:
            System overview dictionary
        """
        overview = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'version': '1.0.0',  # Would get from settings
                'uptime': 'N/A',  # Would calculate from start time
            }
        }
        
        # Get health status if available
        if self.health_checker:
            try:
                import asyncio
                health = asyncio.run(self.health_checker.get_health())
                overview['health'] = health
            except Exception as e:
                logger.error("Failed to get health status", error=str(e))
        
        return overview


def create_dashboard_routes(app: FastAPI, dashboard: MonitoringDashboard):
    """Add dashboard routes to FastAPI app"""
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard():
        """Get monitoring dashboard HTML"""
        return dashboard.get_dashboard_html()
    
    @app.get("/api/v1/health")
    async def get_health():
        """Get system health status"""
        if dashboard.health_checker:
            return await dashboard.health_checker.get_health()
        return {
            'status': 'unknown',
            'message': 'Health checker not configured',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @app.get("/metrics")
    async def get_metrics():
        """Get Prometheus metrics"""
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
