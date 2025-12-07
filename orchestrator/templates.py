"""
Workflow Templates
Predefined workflow templates for common task types
"""

from typing import Dict, Any, List, Optional

# Common task types
TASK_TYPES = {
    'research_and_analyze': 'Research and analyze a topic',
    'code_generation': 'Generate code based on requirements',
    'data_processing': 'Process and transform data',
    'analysis': 'Analyze data or content',
    'synthesis': 'Synthesize information',
    'validation': 'Validate data or code',
    'transformation': 'Transform data format',
    'aggregation': 'Aggregate multiple results',
    'simple': 'Simple single-step task'
}

# Workflow templates
WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    'research_and_analyze': {
        'description': 'Research a topic and analyze results',
        'steps': [
            {
                'step_id': 'research',
                'agent_type': 'research_agent',
                'capabilities_required': ['research', 'web_search'],
                'depends_on': [],
                'output_key': 'research_data',
                'estimated_time': 60,  # seconds
                'estimated_cost': 0.01
            },
            {
                'step_id': 'analyze',
                'agent_type': 'analysis_agent',
                'capabilities_required': ['analysis', 'data_processing'],
                'depends_on': ['research'],
                'output_key': 'analysis_results',
                'estimated_time': 30,
                'estimated_cost': 0.005
            },
            {
                'step_id': 'synthesize',
                'agent_type': 'synthesis_agent',
                'capabilities_required': ['synthesis', 'writing'],
                'depends_on': ['analyze'],
                'output_key': 'final_result',
                'estimated_time': 45,
                'estimated_cost': 0.008
            }
        ]
    },
    
    'code_generation': {
        'description': 'Generate code based on requirements',
        'steps': [
            {
                'step_id': 'analyze_requirements',
                'agent_type': 'requirements_agent',
                'capabilities_required': ['analysis', 'requirements'],
                'depends_on': [],
                'output_key': 'requirements',
                'estimated_time': 30,
                'estimated_cost': 0.005
            },
            {
                'step_id': 'generate_code',
                'agent_type': 'code_generation_agent',
                'capabilities_required': ['code_generation'],
                'depends_on': ['analyze_requirements'],
                'output_key': 'generated_code',
                'estimated_time': 120,
                'estimated_cost': 0.02
            },
            {
                'step_id': 'validate_code',
                'agent_type': 'validation_agent',
                'capabilities_required': ['validation', 'code_review'],
                'depends_on': ['generate_code'],
                'output_key': 'validated_code',
                'estimated_time': 20,
                'estimated_cost': 0.003
            }
        ]
    },
    
    'data_processing': {
        'description': 'Process and transform data',
        'steps': [
            {
                'step_id': 'validate_input',
                'agent_type': 'validation_agent',
                'capabilities_required': ['validation'],
                'depends_on': [],
                'output_key': 'validated_data',
                'estimated_time': 10,
                'estimated_cost': 0.002
            },
            {
                'step_id': 'transform',
                'agent_type': 'transformation_agent',
                'capabilities_required': ['transformation', 'data_processing'],
                'depends_on': ['validate_input'],
                'output_key': 'transformed_data',
                'estimated_time': 30,
                'estimated_cost': 0.005
            }
        ]
    },
    
    'parallel_analysis': {
        'description': 'Analyze multiple items in parallel',
        'steps': [
            {
                'step_id': 'analyze_item_1',
                'agent_type': 'analysis_agent',
                'capabilities_required': ['analysis'],
                'depends_on': [],
                'output_key': 'result_1',
                'estimated_time': 30,
                'estimated_cost': 0.005,
                'parallel': True
            },
            {
                'step_id': 'analyze_item_2',
                'agent_type': 'analysis_agent',
                'capabilities_required': ['analysis'],
                'depends_on': [],
                'output_key': 'result_2',
                'estimated_time': 30,
                'estimated_cost': 0.005,
                'parallel': True
            },
            {
                'step_id': 'aggregate',
                'agent_type': 'aggregation_agent',
                'capabilities_required': ['aggregation'],
                'depends_on': ['analyze_item_1', 'analyze_item_2'],
                'output_key': 'aggregated_result',
                'estimated_time': 20,
                'estimated_cost': 0.003
            }
        ]
    },
    
    'simple': {
        'description': 'Simple single-step task',
        'steps': [
            {
                'step_id': 'execute',
                'agent_type': 'generic_agent',
                'capabilities_required': ['generic'],
                'depends_on': [],
                'output_key': 'result',
                'estimated_time': 10,
                'estimated_cost': 0.001
            }
        ]
    }
}


def get_template(template_name: str) -> Dict[str, Any]:
    """Get a workflow template by name"""
    return WORKFLOW_TEMPLATES.get(template_name)


def list_templates() -> List[str]:
    """List all available template names"""
    return list(WORKFLOW_TEMPLATES.keys())


def match_template(task_type: str) -> Optional[str]:
    """
    Match a task type to a template
    
    Args:
        task_type: Task type string
        
    Returns:
        Template name or None
    """
    task_lower = task_type.lower()
    
    # Exact match
    if task_type in WORKFLOW_TEMPLATES:
        return task_type
    
    # Pattern matching
    if 'research' in task_lower and 'analyze' in task_lower:
        return 'research_and_analyze'
    
    if 'code' in task_lower or ('generate' in task_lower and 'code' in task_lower):
        return 'code_generation'
    
    if 'process' in task_lower and 'data' in task_lower:
        return 'data_processing'
    
    if 'parallel' in task_lower:
        return 'parallel_analysis'
    
    # Default to simple
    return 'simple'

