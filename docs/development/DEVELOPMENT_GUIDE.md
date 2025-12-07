# Development Guide
## Orchestrator AI - Development & Testing

**Last Updated:** 2024-12-07

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (tested with 3.9.6)
- Docker and Docker Compose
- Virtual environment (venv)

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Start Redis and PostgreSQL
docker-compose -f docker-compose.dev.yml up -d redis postgres

# Or use the startup script
./scripts/dev_start.sh
```

### 3. Start API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server with hot reload
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access API

- **API Base URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **API Health:** http://localhost:8000/api/v1/health

---

## 🧪 Testing

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test category
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/performance/ -v   # Performance tests
pytest tests/security/ -v      # Security tests
```

### Test API Endpoints

```bash
# Use the test script
./scripts/test_api.sh

# Or manually test with curl
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health

# Submit a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "simple",
    "input": {"message": "Hello, World!"}
  }'
```

---

## 📝 Development Workflow

### 1. Code Structure

```
orchestrator-ai/
├── agents/           # Agent implementations
├── api/              # FastAPI application
├── config/           # Configuration
├── database/         # Database models and connections
├── monitoring/       # Logging, metrics, health checks
├── orchestrator/    # Core orchestration logic
├── security/         # Authentication, authorization
├── state/            # State management
└── tests/            # Test suites
```

### 2. Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code style (use black, isort)
   - Add tests for new features
   - Update documentation

3. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

4. **Check Code Quality**
   ```bash
   black . --check
   isort . --check
   flake8 .
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

### 3. Hot Reload

The development server runs with `--reload` flag, so changes to Python files will automatically restart the server.

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Database
DATABASE_URL=postgresql://orchestrator:password@localhost:5432/orchestrator

# Security (optional)
API_KEY=your-api-key
SECRET_KEY=your-secret-key
```

### Default Configuration

If no `.env` file exists, the system uses defaults:
- API: `0.0.0.0:8000`
- Redis: `localhost:6379`
- Database: SQLite (in-memory if not configured)
- Log Level: `INFO`

---

## 🐛 Debugging

### View Logs

```bash
# Application logs (if LOG_FILE is set)
tail -f logs/orchestrator.log

# Docker logs
docker-compose -f docker-compose.dev.yml logs -f orchestrator
docker-compose -f docker-compose.dev.yml logs -f redis
docker-compose -f docker-compose.dev.yml logs -f postgres
```

### Debug Mode

Set `LOG_LEVEL=DEBUG` in `.env` or environment variable:

```bash
export LOG_LEVEL=DEBUG
uvicorn api.main:app --reload
```

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Database Connection Error**
   - Check PostgreSQL is running: `docker ps`
   - Verify connection string in `.env`
   - Check database exists

3. **Redis Connection Error**
   - Check Redis is running: `docker ps`
   - Test connection: `docker exec orchestrator-ai-redis-1 redis-cli ping`

---

## 📊 Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# API health (includes system status)
curl http://localhost:8000/api/v1/health
```

### Metrics

If metrics are enabled:
- **Metrics Endpoint:** http://localhost:9090/metrics
- **Prometheus:** http://localhost:9090 (if running)

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧩 Adding New Features

### 1. Add New Agent

```python
# agents/specialized/my_agent.py
from agents.base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent",
            name="My Agent",
            capabilities=["my_capability"]
        )
    
    async def execute(self, task: dict) -> dict:
        # Your implementation
        return {"status": "success", "result": "..."}
```

### 2. Add New API Endpoint

```python
# api/routes.py
@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

### 3. Add New Workflow Template

```python
# orchestrator/templates.py
WORKFLOW_TEMPLATES['my_workflow'] = {
    'description': 'My workflow',
    'steps': [
        {
            'step_id': 'step1',
            'agent_type': 'my_agent',
            'depends_on': [],
            'input_data': {}
        }
    ]
}
```

---

## 🧪 Writing Tests

### Unit Test Example

```python
# tests/unit/test_my_feature.py
import pytest
from my_module import MyClass

def test_my_feature():
    obj = MyClass()
    result = obj.method()
    assert result == expected_value
```

### Integration Test Example

```python
# tests/integration/test_my_workflow.py
@pytest.mark.asyncio
async def test_workflow_execution(orchestrator):
    task = {'type': 'my_workflow', 'input': {}}
    result = await orchestrator.execute(task)
    assert result['status'] == 'completed'
```

---

## 📦 Dependencies

### Core Dependencies
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- SQLAlchemy: Database ORM
- Redis: State management
- Structlog: Structured logging

### Development Dependencies
- pytest: Testing framework
- black: Code formatter
- flake8: Linter
- mypy: Type checker

### Update Dependencies

```bash
# Update requirements
pip freeze > requirements.txt

# Install new dependency
pip install package-name
pip install -r requirements.txt
```

---

## 🚢 Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose up -d
```

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Code Review:** See `CODE_REVIEW.md`
- **Test Results:** See `TEST_RESULTS.md`
- **Architecture:** See `docs/ARCHITECTURE.md`

---

## 🆘 Getting Help

1. Check logs for errors
2. Review test results
3. Check API documentation
4. Review code review notes

---

**Happy Coding! 🎉**

