"""
CLI Main
Command-line interface for orchestrator
"""

import json
import sys
import click
from typing import Optional
from pathlib import Path
from monitoring import get_logger
from cli.client import OrchestratorClient, OutputFormatter
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


@click.group()
@click.option(
    '--base-url',
    default=None,
    help='Orchestrator API base URL'
)
@click.option(
    '--api-key',
    default=None,
    envvar='ORCHESTRATOR_API_KEY',
    help='API key for authentication'
)
@click.option(
    '--output',
    type=click.Choice(['json', 'table', 'text']),
    default='text',
    help='Output format'
)
@click.pass_context
def cli(ctx, base_url, api_key, output):
    """Orchestrator AI Agent CLI"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = OrchestratorClient(base_url=base_url, api_key=api_key)
    ctx.obj['formatter'] = OutputFormatter()
    ctx.obj['output'] = output


@cli.command()
@click.argument('task_type')
@click.option(
    '--input',
    'input_file',
    type=click.File('r'),
    help='Input JSON file'
)
@click.option(
    '--input-data',
    help='Input data as JSON string'
)
@click.option(
    '--wait',
    is_flag=True,
    help='Wait for task completion'
)
@click.option(
    '--timeout',
    default=300,
    help='Timeout in seconds when waiting'
)
@click.pass_context
def submit(ctx, task_type, input_file, input_data, wait, timeout):
    """Submit a new task"""
    try:
        # Parse input data
        if input_file:
            input_data_dict = json.load(input_file)
        elif input_data:
            input_data_dict = json.loads(input_data)
        else:
            input_data_dict = {}
        
        # Submit task
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.submit_task(task_type, input_data_dict)
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            click.echo(f"Task submitted: {result.get('task_id')}")
            click.echo(f"Status: {result.get('status')}")
        
        # Wait for completion if requested
        if wait:
            task_id = result.get('task_id')
            click.echo(f"Waiting for task {task_id} to complete...")
            
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = client.get_task_status(task_id)
                current_status = status.get('status')
                
                if current_status in ['completed', 'failed']:
                    if output_format == 'json':
                        click.echo(formatter.format_json(status))
                    else:
                        click.echo(formatter.format_task_status(status))
                    break
                
                time.sleep(2)
            else:
                click.echo(f"Timeout waiting for task completion")
                sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.pass_context
def status(ctx, task_id):
    """Get task status"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.get_task_status(task_id)
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            click.echo(formatter.format_task_status(result))
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.pass_context
def result(ctx, task_id):
    """Get task result"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.get_task_result(task_id)
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            if result.get('result'):
                click.echo(formatter.format_json(result.get('result')))
            else:
                click.echo("No result available")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--status',
    help='Filter by status'
)
@click.option(
    '--limit',
    default=10,
    help='Maximum number of results'
)
@click.option(
    '--offset',
    default=0,
    help='Offset for pagination'
)
@click.pass_context
def list_tasks(ctx, status, limit, offset):
    """List tasks"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.list_tasks(status=status, limit=limit, offset=offset)
        tasks = result.get('tasks', [])
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        elif output_format == 'table':
            if tasks:
                headers = ['Task ID', 'Type', 'Status', 'Created At']
                rows = [
                    [
                        task.get('task_id', 'N/A'),
                        task.get('type', 'N/A'),
                        task.get('status', 'N/A'),
                        task.get('created_at', 'N/A')
                    ]
                    for task in tasks
                ]
                click.echo(formatter.format_table(rows, headers))
            else:
                click.echo("No tasks found")
        else:
            for task in tasks:
                click.echo(f"{task.get('task_id')} - {task.get('type')} - {task.get('status')}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.pass_context
def cancel(ctx, task_id):
    """Cancel a task"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.cancel_task(task_id)
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            click.echo(f"Task {task_id} cancellation requested")
            click.echo(f"Status: {result.get('status')}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path')
@click.option(
    '--task-type',
    default='code_generation',
    help='Task type for code generation'
)
@click.option(
    '--description',
    help='Description of what to generate'
)
@click.pass_context
def generate(ctx, file_path, task_type, description):
    """Generate code file"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        # Prepare input data
        input_data = {
            'file_path': file_path,
            'description': description or f"Generate code for {file_path}"
        }
        
        # Submit generation task
        result = client.submit_task(task_type, input_data)
        task_id = result.get('task_id')
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            click.echo(f"Code generation task submitted: {task_id}")
            click.echo(f"File: {file_path}")
            click.echo("Waiting for completion...")
        
        # Wait for completion
        import time
        start_time = time.time()
        timeout = 300
        
        while time.time() - start_time < timeout:
            status = client.get_task_status(task_id)
            current_status = status.get('status')
            
            if current_status == 'completed':
                result_data = client.get_task_result(task_id)
                generated_code = result_data.get('result', {}).get('code')
                
                if generated_code:
                    # Write to file
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(generated_code)
                    click.echo(f"Code generated and saved to {file_path}")
                else:
                    click.echo("No code generated")
                break
            
            elif current_status == 'failed':
                click.echo(f"Generation failed: {status.get('error')}")
                sys.exit(1)
            
            time.sleep(2)
        else:
            click.echo("Timeout waiting for code generation")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    try:
        client = ctx.obj['client']
        formatter = ctx.obj['formatter']
        output_format = ctx.obj['output']
        
        result = client.get_health()
        
        if output_format == 'json':
            click.echo(formatter.format_json(result))
        else:
            status = result.get('status', 'unknown')
            click.echo(f"System Status: {status}")
            
            checks = result.get('checks', {})
            if checks:
                click.echo("\nHealth Checks:")
                for name, check in checks.items():
                    check_status = check.get('status', 'unknown')
                    message = check.get('message', '')
                    click.echo(f"  {name}: {check_status} - {message}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

