"""
Agent Selector
Selects appropriate agents for tasks
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from monitoring import get_logger
from agents.registry import AgentRegistry
from agents.base import BaseAgent
from orchestrator.planner import WorkflowStep

logger = get_logger(__name__)


class AgentScore:
    """Represents an agent score for selection"""
    
    def __init__(
        self,
        agent_id: str,
        agent: BaseAgent,
        capability_score: float,
        load_score: float,
        cost_score: float,
        health_score: float,
        total_score: float
    ):
        self.agent_id = agent_id
        self.agent = agent
        self.capability_score = capability_score
        self.load_score = load_score
        self.cost_score = cost_score
        self.health_score = health_score
        self.total_score = total_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'capability_score': self.capability_score,
            'load_score': self.load_score,
            'cost_score': self.cost_score,
            'health_score': self.health_score,
            'total_score': self.total_score
        }


class AgentSelector:
    """Selects appropriate agents for tasks"""
    
    def __init__(self, registry: AgentRegistry):
        """
        Initialize agent selector
        
        Args:
            registry: AgentRegistry instance
        """
        self.registry = registry
        self.workload_tracker: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Scoring weights (can be configured)
        self.scoring_weights = {
            'capability': 0.4,
            'load': 0.25,
            'cost': 0.2,
            'health': 0.15
        }
        
        logger.info("AgentSelector initialized")
    
    async def select_for_step(
        self,
        step: WorkflowStep,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAgent]:
        """
        Select the best agent for a workflow step
        
        Args:
            step: WorkflowStep to select agent for
            options: Optional selection options (budget, preferred_agents, etc.)
            
        Returns:
            Selected BaseAgent or None if no suitable agent found
        """
        options = options or {}
        
        logger.info(
            "Selecting agent for step",
            step_id=step.step_id,
            agent_type=step.agent_type
        )
        
        # Find candidates
        candidates = self._find_candidates(step, options)
        
        if not candidates:
            logger.warning("No suitable agents found", step_id=step.step_id)
            return None
        
        # Score candidates
        scores = await self._score_agents(candidates, step, options)
        
        # Select best agent
        best_score = max(scores, key=lambda s: s.total_score)
        
        logger.info(
            "Agent selected",
            step_id=step.step_id,
            agent_id=best_score.agent_id,
            score=best_score.total_score
        )
        
        return best_score.agent
    
    def _find_candidates(
        self,
        step: WorkflowStep,
        options: Dict[str, Any]
    ) -> List[BaseAgent]:
        """
        Find candidate agents for a step
        
        Args:
            step: WorkflowStep
            options: Selection options
            
        Returns:
            List of candidate agents
        """
        # Check for preferred agents
        preferred_agents = options.get('preferred_agents', [])
        if preferred_agents:
            candidates = []
            for agent_id in preferred_agents:
                agent = self.registry.get(agent_id)
                if agent and self._is_suitable(agent, step):
                    candidates.append(agent)
            if candidates:
                return candidates
        
        # Find by agent type
        candidates = []
        for agent_entry in self.registry.agents.values():
            agent = agent_entry['agent']
            if isinstance(agent, BaseAgent):
                # Check if agent type matches
                # Match by exact agent_id, or if agent_id starts with agent_type, or if agent_type is in capabilities
                if agent.agent_id == step.agent_type or \
                   agent.agent_id.startswith(step.agent_type) or \
                   step.agent_type in agent.capabilities:
                    if self._is_suitable(agent, step):
                        candidates.append(agent)
        
        # If no exact match, find by capability
        if not candidates:
            # Extract required capabilities from step
            required_capabilities = self._extract_required_capabilities(step)
            
            for capability in required_capabilities:
                candidates.extend(self.registry.find_by_capability(capability))
                if candidates:
                    break
        
        # Filter by status
        candidates = [a for a in candidates if a.status == 'active']
        
        return candidates
    
    def _is_suitable(self, agent: BaseAgent, step: WorkflowStep) -> bool:
        """Check if agent is suitable for step"""
        # Check if agent is active
        if agent.status != 'active':
            return False
        
        # Check capabilities - agent must have at least one required capability
        # OR if agent_id matches agent_type, it's automatically suitable
        if agent.agent_id == step.agent_type or agent.agent_id.startswith(step.agent_type):
            return True
        
        # Check if agent has any of the required capabilities
        required_capabilities = self._extract_required_capabilities(step)
        if required_capabilities and required_capabilities != ['generic']:
            # Agent must have at least one required capability
            if not any(agent.has_capability(cap) for cap in required_capabilities):
                return False
        
        return True
    
    def _extract_required_capabilities(self, step: WorkflowStep) -> List[str]:
        """Extract required capabilities from step"""
        capabilities = []
        
        # Check if step has explicit capabilities
        if hasattr(step, 'capabilities_required'):
            capabilities.extend(step.capabilities_required)
        
        # Extract from agent type
        agent_type = step.agent_type
        if agent_type:
            capabilities.append(agent_type)
            # Remove '_agent' suffix if present
            if agent_type.endswith('_agent'):
                capabilities.append(agent_type[:-6])
        
        return capabilities if capabilities else ['generic']
    
    async def _score_agents(
        self,
        agents: List[BaseAgent],
        step: WorkflowStep,
        options: Dict[str, Any]
    ) -> List[AgentScore]:
        """
        Score agents for selection
        
        Args:
            agents: List of candidate agents
            step: WorkflowStep
            options: Selection options
            
        Returns:
            List of AgentScore objects
        """
        scores = []
        
        for agent in agents:
            capability_score = self._score_capability(agent, step)
            load_score = self._score_load(agent)
            cost_score = self._score_cost(agent, step, options)
            health_score = await self._score_health(agent)
            
            # Calculate weighted total score
            total_score = (
                capability_score * self.scoring_weights['capability'] +
                load_score * self.scoring_weights['load'] +
                cost_score * self.scoring_weights['cost'] +
                health_score * self.scoring_weights['health']
            )
            
            scores.append(AgentScore(
                agent_id=agent.agent_id,
                agent=agent,
                capability_score=capability_score,
                load_score=load_score,
                cost_score=cost_score,
                health_score=health_score,
                total_score=total_score
            ))
        
        return scores
    
    def _score_capability(self, agent: BaseAgent, step: WorkflowStep) -> float:
        """
        Score agent based on capability match (0.0 to 1.0)
        
        Higher score = better capability match
        """
        required_capabilities = self._extract_required_capabilities(step)
        
        if not required_capabilities:
            return 1.0
        
        matches = sum(1 for cap in required_capabilities if agent.has_capability(cap))
        score = matches / len(required_capabilities)
        
        return score
    
    def _score_load(self, agent: BaseAgent) -> float:
        """
        Score agent based on current load (0.0 to 1.0)
        
        Higher score = less load (better)
        """
        agent_id = agent.agent_id
        workload = self.workload_tracker.get(agent_id, {})
        
        # Get current task count
        current_tasks = workload.get('current_tasks', 0)
        max_tasks = workload.get('max_concurrent_tasks', 5)
        
        if max_tasks == 0:
            return 1.0
        
        utilization = current_tasks / max_tasks
        # Inverse score: less utilization = higher score
        score = 1.0 - min(utilization, 1.0)
        
        return max(score, 0.0)
    
    def _score_cost(self, agent: BaseAgent, step: WorkflowStep, options: Dict[str, Any]) -> float:
        """
        Score agent based on cost (0.0 to 1.0)
        
        Higher score = lower cost (better)
        """
        agent_id = agent.agent_id
        
        # Get agent cost from metadata
        agent_entry = self.registry.agents.get(agent_id, {})
        metadata = agent_entry.get('metadata', {})
        cost_per_request = metadata.get('cost_per_request', 0.01)
        
        # Check budget constraint
        budget = options.get('budget')
        if budget is not None and cost_per_request > budget:
            return 0.0  # Over budget
        
        # Normalize cost (assuming max cost is 0.1)
        max_cost = 0.1
        normalized_cost = min(cost_per_request / max_cost, 1.0)
        
        # Inverse score: lower cost = higher score
        score = 1.0 - normalized_cost
        
        return max(score, 0.0)
    
    async def _score_health(self, agent: BaseAgent) -> float:
        """
        Score agent based on health (0.0 to 1.0)
        
        Higher score = better health
        """
        health = await agent.health_check()
        
        if not health.get('healthy', False):
            return 0.0
        
        # Get metrics if available
        agent_id = agent.agent_id
        metrics = self.agent_metrics.get(agent_id, {})
        
        # Calculate health score based on metrics
        success_rate = metrics.get('success_rate', 1.0)
        avg_latency = metrics.get('avg_latency', 100)
        
        # Normalize latency (assume max acceptable is 1000ms)
        latency_score = max(0.0, 1.0 - (avg_latency / 1000.0))
        
        # Combined health score
        score = (success_rate * 0.7 + latency_score * 0.3)
        
        return score
    
    def track_workload(self, agent_id: str, task_count: int):
        """
        Track agent workload
        
        Args:
            agent_id: Agent ID
            task_count: Current number of tasks
        """
        if agent_id not in self.workload_tracker:
            self.workload_tracker[agent_id] = {
                'current_tasks': 0,
                'max_concurrent_tasks': 5,
                'last_updated': datetime.utcnow()
            }
        
        self.workload_tracker[agent_id]['current_tasks'] = task_count
        self.workload_tracker[agent_id]['last_updated'] = datetime.utcnow()
    
    def increment_workload(self, agent_id: str):
        """Increment agent workload"""
        if agent_id not in self.workload_tracker:
            self.track_workload(agent_id, 0)
        self.workload_tracker[agent_id]['current_tasks'] += 1
    
    def decrement_workload(self, agent_id: str):
        """Decrement agent workload"""
        if agent_id in self.workload_tracker:
            self.workload_tracker[agent_id]['current_tasks'] = max(
                0,
                self.workload_tracker[agent_id]['current_tasks'] - 1
            )
    
    def update_agent_metrics(
        self,
        agent_id: str,
        success_rate: float,
        avg_latency: float
    ):
        """
        Update agent performance metrics
        
        Args:
            agent_id: Agent ID
            success_rate: Success rate (0.0 to 1.0)
            avg_latency: Average latency in milliseconds
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = {}
        
        self.agent_metrics[agent_id]['success_rate'] = success_rate
        self.agent_metrics[agent_id]['avg_latency'] = avg_latency
        self.agent_metrics[agent_id]['last_updated'] = datetime.utcnow().isoformat()
    
    def get_agent_load(self, agent_id: str) -> Dict[str, Any]:
        """Get current agent workload"""
        return self.workload_tracker.get(agent_id, {
            'current_tasks': 0,
            'max_concurrent_tasks': 5
        })
    
    def set_scoring_weights(self, weights: Dict[str, float]):
        """
        Set scoring weights
        
        Args:
            weights: Dictionary with weight values (must sum to 1.0)
        """
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning("Scoring weights don't sum to 1.0, normalizing", total=total)
            weights = {k: v/total for k, v in weights.items()}
        
        self.scoring_weights.update(weights)
        logger.info("Scoring weights updated", weights=self.scoring_weights)
