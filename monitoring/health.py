"""
Health Checks
System and agent health monitoring
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from monitoring import get_logger
from agents.registry import AgentRegistry

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Health check result"""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize health check result
        
        Args:
            name: Check name
            status: Health status
            message: Optional status message
            details: Optional detailed information
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class HealthMonitor:
    """System health monitor"""
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None
    ):
        """
        Initialize health monitor
        
        Args:
            registry: Optional AgentRegistry instance
        """
        self.registry = registry
        self.checks: Dict[str, Callable] = {}
        logger.info("HealthMonitor initialized")
    
    def register_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheck]
    ):
        """
        Register a health check function
        
        Args:
            name: Check name
            check_func: Function that returns HealthCheck
        """
        self.checks[name] = check_func
        logger.info("Health check registered", check_name=name)
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks
        
        Returns:
            Overall health status and individual checks
        """
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = result.to_dict()
                
                # Determine overall status
                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                logger.error(
                    "Health check failed",
                    check_name=name,
                    error=str(e)
                )
                results[name] = {
                    'name': name,
                    'status': HealthStatus.UNHEALTHY,
                    'message': f"Check failed: {str(e)}",
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_status = HealthStatus.UNHEALTHY
        
        return {
            'status': overall_status,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }


class SystemHealthChecker:
    """System health checker with built-in checks"""
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        state_store: Optional[Any] = None,
        message_broker: Optional[Any] = None
    ):
        """
        Initialize system health checker
        
        Args:
            registry: AgentRegistry instance
            state_store: StateStore instance
            message_broker: MessageBroker instance
        """
        self.registry = registry
        self.state_store = state_store
        self.message_broker = message_broker
        self.monitor = HealthMonitor(registry)
        
        # Register built-in checks
        self._register_checks()
        
        logger.info("SystemHealthChecker initialized")
    
    def _register_checks(self):
        """Register built-in health checks"""
        if self.registry:
            self.monitor.register_check("agents", self._check_agents)
        
        if self.state_store:
            self.monitor.register_check("state_store", self._check_state_store)
        
        if self.message_broker:
            self.monitor.register_check("message_broker", self._check_message_broker)
    
    async def _check_agents(self) -> HealthCheck:
        """Check agent health"""
        if not self.registry:
            return HealthCheck(
                "agents",
                HealthStatus.UNKNOWN,
                "AgentRegistry not available"
            )
        
        agents = self.registry.list_agents()
        active_agents = [
            agent for agent in agents
            if agent.status == 'active'
        ]
        
        total = len(agents)
        active = len(active_agents)
        
        if total == 0:
            status = HealthStatus.DEGRADED
            message = "No agents registered"
        elif active == 0:
            status = HealthStatus.UNHEALTHY
            message = "No active agents"
        elif active < total * 0.5:
            status = HealthStatus.DEGRADED
            message = f"Less than 50% of agents are active ({active}/{total})"
        else:
            status = HealthStatus.HEALTHY
            message = f"{active}/{total} agents active"
        
        return HealthCheck(
            "agents",
            status,
            message,
            {
                'total_agents': total,
                'active_agents': active,
                'inactive_agents': total - active
            }
        )
    
    async def _check_state_store(self) -> HealthCheck:
        """Check state store health"""
        if not self.state_store:
            return HealthCheck(
                "state_store",
                HealthStatus.UNKNOWN,
                "StateStore not available"
            )
        
        try:
            # Try to list workflows (basic connectivity check)
            if hasattr(self.state_store, 'list_workflows'):
                if asyncio.iscoroutinefunction(self.state_store.list_workflows):
                    workflows = await self.state_store.list_workflows()
                else:
                    workflows = self.state_store.list_workflows()
            else:
                workflows = []
            
            return HealthCheck(
                "state_store",
                HealthStatus.HEALTHY,
                "State store is operational",
                {'workflows_count': len(workflows)}
            )
        except Exception as e:
            return HealthCheck(
                "state_store",
                HealthStatus.UNHEALTHY,
                f"State store check failed: {str(e)}"
            )
    
    async def _check_message_broker(self) -> HealthCheck:
        """Check message broker health"""
        if not self.message_broker:
            return HealthCheck(
                "message_broker",
                HealthStatus.UNKNOWN,
                "MessageBroker not available"
            )
        
        try:
            # Check Redis connection
            if hasattr(self.message_broker, 'redis'):
                if self.message_broker.redis:
                    await self.message_broker.redis.ping()
                    return HealthCheck(
                        "message_broker",
                        HealthStatus.HEALTHY,
                        "Message broker is operational"
                    )
            
            return HealthCheck(
                "message_broker",
                HealthStatus.DEGRADED,
                "Message broker not connected"
            )
        except Exception as e:
            return HealthCheck(
                "message_broker",
                HealthStatus.UNHEALTHY,
                f"Message broker check failed: {str(e)}"
            )
    
    async def get_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        return await self.monitor.check_all()
    
    async def is_healthy(self) -> bool:
        """Check if system is healthy"""
        health = await self.get_health()
        return health['status'] == HealthStatus.HEALTHY

