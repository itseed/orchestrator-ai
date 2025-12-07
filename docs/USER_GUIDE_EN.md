# 📖 User Guide
## Orchestrator AI Agent - Complete User Guide

**Version:** 1.0.0  
**Last Updated:** 2024-12-07

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Initial Setup](#initial-setup)
3. [Basic Usage](#basic-usage)
4. [API Usage](#api-usage)
5. [Creating Custom Agents](#creating-custom-agents)
6. [Using Specialized Agents](#using-specialized-agents)
7. [Workflow Management](#workflow-management)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## 🚀 Installation

### System Requirements

- Python 3.9 or higher
- Docker and Docker Compose (for production)
- Redis (for message broker and state store)
- PostgreSQL (for persistent storage - optional)

### Installation Steps

#### 1. Clone Repository

```bash
git clone <repository-url>
cd orchestrator-ai
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with appropriate values
```

#### 5. Start Services

```bash
# Start Redis and PostgreSQL
docker-compose -f docker-compose.dev.yml up -d redis postgres

# Or use script
./scripts/dev_start.sh
```

---

## ⚙️ Initial Setup

### Environment Variables

Create `.env` file in root directory:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Database (optional)
DATABASE_URL=postgresql://orchestrator:password@localhost:5432/orchestrator

# LLM Configuration (for specialized agents)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_GEMINI_API_KEY=your-google-gemini-api-key

# Security (optional)
API_KEY=your-api-key
SECRET_KEY=your-secret-key
```

### Start API Server

```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# View API documentation
# Open browser: http://localhost:8000/docs
```

---

## 🎯 Basic Usage

### 1. Create Simple Task

```python
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from state.store import StateStore

# Initialize
registry = AgentRegistry()
state_store = StateStore()
orchestrator = OrchestratorEngine(registry=registry, state_store=state_store)

# Create task
task = {
    "type": "simple",
    "input": {
        "message": "Hello, World!"
    }
}

# Execute
result = await orchestrator.execute(task)
print(result)
```

### 2. Use via API

```bash
# Submit task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "simple",
    "input": {
      "message": "Hello from API"
    }
  }'

# Check status
curl http://localhost:8000/api/v1/tasks/{task_id}

# Get result
curl http://localhost:8000/api/v1/tasks/{task_id}/result
```

### 3. Use via CLI

```bash
# Submit task
python -m cli.main submit --type simple --input '{"message": "Hello"}'

# Check status
python -m cli.main status {task_id}

# Get result
python -m cli.main result {task_id}

# List tasks
python -m cli.main list
```

---

## 🔌 API Usage

### Base URL

```
http://localhost:8000/api/v1
```

### Main Endpoints

#### 1. Submit Task

```http
POST /api/v1/tasks
Content-Type: application/json

{
  "type": "task_type",
  "input": {
    "key": "value"
  },
  "workflow": "optional_workflow_name",
  "callback_url": "https://your-callback-url.com/webhook",
  "metadata": {
    "custom": "data"
  }
}
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "workflow_id": "workflow-uuid",
  "status": "pending",
  "created_at": "2024-12-07T10:00:00Z"
}
```

#### 2. Get Task Status

```http
GET /api/v1/tasks/{task_id}
```

#### 3. Get Task Result

```http
GET /api/v1/tasks/{task_id}/result
```

#### 4. List Tasks

```http
GET /api/v1/tasks?limit=10&offset=0&status=completed
```

#### 5. Health Check

```http
GET /api/v1/health
```

---

## 🤖 Creating Custom Agents

### 1. Create Agent Class

```python
from agents.base import BaseAgent
from typing import Dict, Any

class MyCustomAgent(BaseAgent):
    """Custom agent for specific tasks"""
    
    def __init__(self):
        super().__init__(
            agent_id="my_custom_agent",
            name="My Custom Agent",
            capabilities=["custom_task", "data_processing"],
            description="Agent for special data processing"
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task
        
        Args:
            task: Task dictionary with input data
            
        Returns:
            Result dictionary
        """
        try:
            input_data = task.get("input", {})
            result = self._process_data(input_data)
            
            return {
                "status": "success",
                "result": result,
                "message": "Task completed successfully"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data"""
        # Your processing logic here
        return {"processed": data}
```

### 2. Register Agent

```python
from agents.registry import AgentRegistry

registry = AgentRegistry()
my_agent = MyCustomAgent()
registry.register(my_agent)
```

---

## 🎨 Using Specialized Agents

### Code Generation Agent

Generate code from description:

```python
task = {
    "type": "code_generation",
    "input": {
        "file_path": "src/utils.py",
        "description": "Create email validator function",
        "language": "python",
        "write_to_file": True
    }
}
```

**LLM Priority:**
1. Google Gemini (if `GOOGLE_GEMINI_API_KEY` is set)
2. OpenAI (if `OPENAI_API_KEY` is set)
3. Anthropic (if `ANTHROPIC_API_KEY` is set)
4. Fallback template

### Research Agent

Search and summarize information:

```python
task = {
    "type": "research",
    "input": {
        "query": "Latest trends in AI",
        "sources": ["web", "academic"],
        "max_results": 10,
        "include_citations": True
    }
}
```

### Analysis Agent

Analyze data and generate insights:

```python
task = {
    "type": "analysis",
    "input": {
        "data": {
            "sales": [100, 150, 200, 180, 220],
            "months": ["Jan", "Feb", "Mar", "Apr", "May"]
        },
        "analysis_type": "trend",
        "insights": True,
        "visualization": False
    }
}
```

---

## 📊 Workflow Management

### Create Custom Workflow

```python
from orchestrator.planner import TaskPlanner
from orchestrator.templates import WorkflowTemplate

# Create workflow template
template = WorkflowTemplate(
    name="custom_workflow",
    description="Custom workflow example",
    steps=[
        {
            "step_id": "step1",
            "agent_type": "research_agent",
            "depends_on": [],
            "input_data": {"query": "AI trends"}
        },
        {
            "step_id": "step2",
            "agent_type": "analysis_agent",
            "depends_on": ["step1"],
            "input_data": {"data": "{{step1.result}}"}
        }
    ]
)

# Use
planner = TaskPlanner()
workflow = await planner.plan_from_template(template, task_input)
```

### Parallel Execution

Steps without dependencies run in parallel automatically:

```python
workflow = {
    "steps": [
        {"step_id": "step1", "depends_on": []},
        {"step_id": "step2", "depends_on": []},  # Runs parallel with step1
        {"step_id": "step3", "depends_on": ["step1", "step2"]}  # Runs after step1, step2
    ]
}
```

---

## 📈 Monitoring and Observability

### Health Checks

```bash
# System health
curl http://localhost:8000/health

# API health (detailed)
curl http://localhost:8000/api/v1/health
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/metrics
```

### Dashboard

```bash
# Open Grafana dashboard
# URL: http://localhost:3000
# Default credentials: admin/admin
```

### Logs

```bash
# View logs
tail -f logs/orchestrator.log

# Or Docker logs
docker-compose logs -f orchestrator
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. API Server Won't Start

**Issue:** Port 8000 already in use

**Solution:**
```bash
# Check process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

#### 2. Redis Connection Error

**Issue:** Cannot connect to Redis

**Solution:**
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis
docker-compose -f docker-compose.dev.yml up -d redis

# Test connection
docker exec orchestrator-ai-redis-1 redis-cli ping
```

#### 3. Database Connection Error

**Issue:** Cannot connect to PostgreSQL

**Solution:**
```bash
# Check PostgreSQL
docker ps | grep postgres

# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Test connection
docker exec orchestrator-ai-postgres-1 pg_isready -U orchestrator
```

#### 4. LLM API Key Not Working

**Issue:** Agents cannot call LLM

**Solution:**
```bash
# Check API key in .env
cat .env | grep API_KEY

# Check if packages are installed
pip list | grep -E "openai|anthropic|google-generativeai"

# Install missing packages
pip install google-generativeai anthropic openai
```

#### 5. Import Errors

**Issue:** Module not found errors

**Solution:**
```bash
# Check virtual environment
which python  # Should point to venv/bin/python

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 💡 Examples

### Example 1: Simple Echo Task

```python
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from agents.specialized import EchoAgent
from state.store import StateStore

# Setup
registry = AgentRegistry()
state_store = StateStore()
orchestrator = OrchestratorEngine(registry=registry, state_store=state_store)

# Register agent
echo_agent = EchoAgent()
registry.register(echo_agent)

# Execute
task = {
    "type": "echo",
    "input": {"message": "Hello, Orchestrator!"}
}

result = await orchestrator.execute(task)
print(result)
```

### Example 2: Multi-Step Workflow

```python
task = {
    "type": "research_and_analyze",
    "input": {
        "query": "AI trends 2024",
        "analysis_type": "trend"
    }
}

# Orchestrator will:
# 1. Use ResearchAgent to search for information
# 2. Use AnalysisAgent to analyze results
# 3. Return summarized results
result = await orchestrator.execute(task)
```

### Example 3: API Call with Callback

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "code_generation",
    "input": {
      "file_path": "src/validator.py",
      "description": "Create email validator function",
      "language": "python"
    },
    "callback_url": "https://your-app.com/webhook/task-complete"
  }'
```

### Example 4: CLI Usage

```bash
# Submit task
python -m cli.main submit \
  --type research \
  --input '{"query": "Python best practices"}'

# Monitor task
python -m cli.main status {task_id}

# Get result
python -m cli.main result {task_id} --format json
```

---

## 📚 Additional Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Development Guide](../development/README_DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/docs) (when server is running)
- [Code Review](CODE_REVIEW.md)
- [Test Results](../testing/TEST_RESULTS.md)

---

## 🆘 Getting Help

1. Check [Troubleshooting](#troubleshooting) section
2. View [API Documentation](http://localhost:8000/docs)
3. Check logs for error messages
4. Review [GitHub Issues](repository-url/issues)

---

## 📝 Changelog

### Version 1.0.0 (2024-12-07)
- Initial release
- Support for multiple LLM providers (OpenAI, Anthropic, Google Gemini)
- Specialized agents (Code, Research, Analysis)
- REST API and CLI tools
- Comprehensive monitoring and health checks

---

**Happy Orchestrating! 🚀**

