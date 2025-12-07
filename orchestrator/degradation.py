"""
Graceful Degradation
Fallback mechanisms and alternative agent selection
"""

from typing import Dict, Any, List, Optional, Callable
from monitoring import get_logger
from agents.base import BaseAgent
from agents.registry import AgentRegistry
from orchestrator.selector import AgentSelector

logger = get_logger(__name__)


class FallbackStrategy:
    """Fallback strategy configuration"""
    
    def __init__(
        self,
        primary_agent_id: str,
        fallback_agents: List[str],
        fallback_conditions: Optional[List[str]] = None
    ):
        """
        Initialize fallback strategy
        
        Args:
            primary_agent_id: Primary agent ID
            fallback_agents: List of fallback agent IDs in order of preference
            fallback_conditions: List of conditions that trigger fallback
        """
        self.primary_agent_id = primary_agent_id
        self.fallback_agents = fallback_agents
        self.fallback_conditions = fallback_conditions or [
            "timeout",
            "error_rate > 50%",
            "unavailable",
            "circuit_breaker_open"
        ]
        
        logger.info(
            "FallbackStrategy created",
            primary=primary_agent_id,
            fallbacks=fallback_agents
        )
    
    def should_fallback(
        self,
        error: Optional[Exception] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if fallback should be triggered
        
        Args:
            error: Exception that occurred
            error_message: Error message
            metrics: Optional metrics dictionary
            
        Returns:
            True if should fallback
        """
        error_msg = (error_message or str(error) or "").lower()
        
        # Check error conditions
        for condition in self.fallback_conditions:
            if condition.lower() in ["timeout", "timed out"]:
                if "timeout" in error_msg or "timed out" in error_msg:
                    return True
            
            if condition.lower() == "unavailable":
                if "unavailable" in error_msg or "not found" in error_msg:
                    return True
            
            if condition.lower() == "circuit_breaker_open":
                if "circuit breaker" in error_msg or "circuit_breaker" in error_msg:
                    return True
            
            if condition.startswith("error_rate >"):
                # Parse error rate condition
                if metrics and 'error_rate' in metrics:
                    threshold = float(condition.split(">")[-1].strip().replace("%", ""))
                    if metrics['error_rate'] > threshold:
                        return True
        
        return False


class GracefulDegradation:
    """Graceful degradation manager"""
    
    def __init__(
        self,
        registry: AgentRegistry,
        selector: AgentSelector
    ):
        """
        Initialize graceful degradation
        
        Args:
            registry: AgentRegistry instance
            selector: AgentSelector instance
        """
        self.registry = registry
        self.selector = selector
        self.fallback_strategies: Dict[str, FallbackStrategy] = {}
        logger.info("GracefulDegradation initialized")
    
    def register_fallback(
        self,
        step_id: str,
        strategy: FallbackStrategy
    ):
        """
        Register fallback strategy for a step
        
        Args:
            step_id: Step ID
            strategy: FallbackStrategy instance
        """
        self.fallback_strategies[step_id] = strategy
        logger.info(
            "Fallback strategy registered",
            step_id=step_id,
            primary=strategy.primary_agent_id,
            fallbacks=len(strategy.fallback_agents)
        )
    
    async def get_agent_with_fallback(
        self,
        step_id: str,
        step: Any,
        error: Optional[Exception] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAgent]:
        """
        Get agent with fallback support
        
        Args:
            step_id: Step ID
            step: WorkflowStep instance
            error: Optional error that occurred
            options: Optional execution options
            
        Returns:
            Agent instance or None
        """
        strategy = self.fallback_strategies.get(step_id)
        
        if not strategy:
            # No fallback strategy, use normal selection
            return await self.selector.select_for_step(step, options or {})
        
        # Try primary agent first
        primary_agent = self.registry.get_agent(strategy.primary_agent_id)
        
        if primary_agent and primary_agent.status == 'active':
            # Check if should use fallback
            if error and strategy.should_fallback(error=error):
                logger.warning(
                    "Fallback triggered",
                    step_id=step_id,
                    primary=strategy.primary_agent_id,
                    error=str(error)
                )
            else:
                return primary_agent
        
        # Try fallback agents
        for fallback_id in strategy.fallback_agents:
            fallback_agent = self.registry.get_agent(fallback_id)
            
            if fallback_agent and fallback_agent.status == 'active':
                logger.info(
                    "Using fallback agent",
                    step_id=step_id,
                    fallback=fallback_id,
                    primary=strategy.primary_agent_id
                )
                return fallback_agent
        
        # Try normal selection as last resort
        logger.warning(
            "All fallback agents failed, trying normal selection",
            step_id=step_id
        )
        return await self.selector.select_for_step(step, options or {})
    
    async def execute_with_fallback(
        self,
        step_id: str,
        step: Any,
        execute_func: Callable,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute with fallback support
        
        Args:
            step_id: Step ID
            step: WorkflowStep instance
            execute_func: Function to execute (takes agent as argument)
            options: Optional execution options
            
        Returns:
            Execution result
            
        Raises:
            Exception if all attempts fail
        """
        strategy = self.fallback_strategies.get(step_id)
        
        if not strategy:
            # No fallback, execute normally
            agent = await self.selector.select_for_step(step, options or {})
            if not agent:
                raise ValueError(f"No agent found for step {step_id}")
            return await execute_func(agent)
        
        # Try primary agent
        primary_agent = self.registry.get_agent(strategy.primary_agent_id)
        if primary_agent and primary_agent.status == 'active':
            try:
                return await execute_func(primary_agent)
            except Exception as e:
                if not strategy.should_fallback(error=e):
                    raise
        
        # Try fallback agents
        last_error = None
        for fallback_id in strategy.fallback_agents:
            fallback_agent = self.registry.get_agent(fallback_id)
            
            if fallback_agent and fallback_agent.status == 'active':
                try:
                    logger.info(
                        "Trying fallback agent",
                        step_id=step_id,
                        fallback=fallback_id
                    )
                    return await execute_func(fallback_agent)
                except Exception as e:
                    last_error = e
                    logger.warning(
                        "Fallback agent failed",
                        step_id=step_id,
                        fallback=fallback_id,
                        error=str(e)
                    )
                    continue
        
        # All failed
        if last_error:
            raise last_error
        raise RuntimeError(f"All agents failed for step {step_id}")


class PartialResultHandler:
    """Handle partial results when some steps fail"""
    
    @staticmethod
    def merge_partial_results(
        results: Dict[str, Any],
        failed_steps: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Merge partial results from successful steps
        
        Args:
            results: Dictionary of step results
            failed_steps: List of failed step IDs
            options: Optional merge options
            
        Returns:
            Merged partial result
        """
        options = options or {}
        merge_mode = options.get('partial_result_mode', 'include_failures')
        
        if merge_mode == 'exclude_failures':
            # Only include successful results
            partial_results = {
                step_id: result
                for step_id, result in results.items()
                if step_id not in failed_steps
            }
        elif merge_mode == 'include_failures':
            # Include failures with error markers
            partial_results = results.copy()
            for step_id in failed_steps:
                if step_id not in partial_results:
                    partial_results[step_id] = {
                        'status': 'failed',
                        'error': 'Step execution failed'
                    }
        else:
            partial_results = results
        
        return {
            'status': 'partial',
            'results': partial_results,
            'failed_steps': failed_steps,
            'successful_steps': [
                step_id for step_id in results.keys()
                if step_id not in failed_steps
            ]
        }

