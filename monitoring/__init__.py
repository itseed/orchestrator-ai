"""Monitoring and observability"""

# Core imports that don't have circular dependencies
from monitoring.logger import get_logger, configure_logging
from monitoring.metrics import MetricsCollector, get_metrics_collector, start_metrics_server

# Lazy imports to avoid circular dependencies
def _import_health():
    """Lazy import for health module"""
    from monitoring.health import (
        HealthStatus,
        HealthCheck,
        HealthMonitor,
        SystemHealthChecker
    )
    return HealthStatus, HealthCheck, HealthMonitor, SystemHealthChecker

def _import_tracing():
    """Lazy import for tracing module"""
    from monitoring.tracing import (
        TraceContext,
        Tracer,
        get_tracer,
        get_correlation_id,
        set_correlation_id
    )
    return TraceContext, Tracer, get_tracer, get_correlation_id, set_correlation_id

def _import_dashboard():
    """Lazy import for dashboard module"""
    from monitoring.dashboard import MonitoringDashboard, create_dashboard_routes
    return MonitoringDashboard, create_dashboard_routes

# Export core functions
__all__ = [
    'get_logger',
    'configure_logging',
    'MetricsCollector',
    'get_metrics_collector',
    'start_metrics_server',
]

