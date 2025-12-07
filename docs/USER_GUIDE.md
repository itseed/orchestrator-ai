# 📖 คู่มือการใช้งาน
## Orchestrator AI Agent - User Guide

**เวอร์ชัน:** 1.0.0  
**อัปเดตล่าสุด:** 2024-12-07

---

## 📋 สารบัญ

1. [การติดตั้ง](#การติดตั้ง)
2. [การตั้งค่าเริ่มต้น](#การตั้งค่าเริ่มต้น)
3. [การใช้งานพื้นฐาน](#การใช้งานพื้นฐาน)
4. [การใช้งาน API](#การใช้งาน-api)
5. [การสร้าง Agent ใหม่](#การสร้าง-agent-ใหม่)
6. [การใช้งาน Specialized Agents](#การใช้งาน-specialized-agents)
7. [การจัดการ Workflow](#การจัดการ-workflow)
8. [การติดตามและ Monitoring](#การติดตามและ-monitoring)
9. [การแก้ไขปัญหา](#การแก้ไขปัญหา)
10. [ตัวอย่างการใช้งาน](#ตัวอย่างการใช้งาน)

---

## 🚀 การติดตั้ง

### ความต้องการของระบบ

- Python 3.9 หรือสูงกว่า
- Docker และ Docker Compose (สำหรับ production)
- Redis (สำหรับ message broker และ state store)
- PostgreSQL (สำหรับ persistent storage - optional)

### ขั้นตอนการติดตั้ง

#### 1. Clone Repository

```bash
git clone <repository-url>
cd orchestrator-ai
```

#### 2. สร้าง Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # บน Windows: venv\Scripts\activate
```

#### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

#### 4. ตั้งค่า Environment Variables

```bash
cp .env.example .env
# แก้ไข .env ด้วยค่าที่เหมาะสม
```

#### 5. เริ่ม Services

```bash
# เริ่ม Redis และ PostgreSQL
docker-compose -f docker-compose.dev.yml up -d redis postgres

# หรือใช้ script
./scripts/dev_start.sh
```

---

## ⚙️ การตั้งค่าเริ่มต้น

### Environment Variables

สร้างไฟล์ `.env` ใน root directory:

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

# LLM Configuration (สำหรับ specialized agents)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_GEMINI_API_KEY=your-google-gemini-api-key

# Security (optional)
API_KEY=your-api-key
SECRET_KEY=your-secret-key
```

### เริ่ม API Server

```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### ตรวจสอบการทำงาน

```bash
# Health check
curl http://localhost:8000/health

# ดู API documentation
# เปิดเบราว์เซอร์ไปที่: http://localhost:8000/docs
```

---

## 🎯 การใช้งานพื้นฐาน

### 1. สร้าง Task แบบง่าย

```python
from orchestrator.engine import OrchestratorEngine
from agents.registry import AgentRegistry
from state.store import StateStore

# Initialize
registry = AgentRegistry()
state_store = StateStore()
orchestrator = OrchestratorEngine(registry=registry, state_store=state_store)

# สร้าง task
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

### 2. ใช้งานผ่าน API

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

# ตรวจสอบสถานะ
curl http://localhost:8000/api/v1/tasks/{task_id}

# ดูผลลัพธ์
curl http://localhost:8000/api/v1/tasks/{task_id}/result
```

### 3. ใช้งานผ่าน CLI

```bash
# Submit task
python -m cli.main submit --type simple --input '{"message": "Hello"}'

# ตรวจสอบสถานะ
python -m cli.main status {task_id}

# ดูผลลัพธ์
python -m cli.main result {task_id}

# ดูรายการ tasks
python -m cli.main list
```

---

## 🔌 การใช้งาน API

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints หลัก

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

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "workflow_id": "workflow-uuid",
  "created_at": "2024-12-07T10:00:00Z",
  "updated_at": "2024-12-07T10:01:00Z"
}
```

#### 3. Get Task Result

```http
GET /api/v1/tasks/{task_id}/result
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "result": {
    "output": "task result data"
  }
}
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

## 🤖 การสร้าง Agent ใหม่

### 1. สร้าง Agent Class

```python
from agents.base import BaseAgent
from typing import Dict, Any

class MyCustomAgent(BaseAgent):
    """Custom agent สำหรับงานเฉพาะ"""
    
    def __init__(self):
        super().__init__(
            agent_id="my_custom_agent",
            name="My Custom Agent",
            capabilities=["custom_task", "data_processing"],
            description="Agent สำหรับประมวลผลข้อมูลแบบพิเศษ"
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
            # ดึงข้อมูลจาก task
            input_data = task.get("input", {})
            
            # ประมวลผล
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
        """ประมวลผลข้อมูล"""
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

### 3. ใช้งาน Agent

```python
# ผ่าน orchestrator
task = {
    "type": "custom_task",
    "input": {"data": "some data"}
}
result = await orchestrator.execute(task)

# หรือเรียกใช้โดยตรง
result = await my_agent.execute(task)
```

---

## 🎨 การใช้งาน Specialized Agents

### Code Generation Agent

สร้างโค้ดตามคำอธิบาย:

```python
task = {
    "type": "code_generation",
    "input": {
        "file_path": "src/utils.py",
        "description": "สร้างฟังก์ชันสำหรับ validate email",
        "language": "python",
        "write_to_file": True
    }
}
```

### Research Agent

ค้นหาข้อมูลและสรุป:

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

วิเคราะห์ข้อมูลและสร้าง insights:

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

## 📊 การจัดการ Workflow

### สร้าง Workflow แบบกำหนดเอง

```python
from orchestrator.planner import TaskPlanner
from orchestrator.templates import WorkflowTemplate

# สร้าง workflow template
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

# ใช้งาน
planner = TaskPlanner()
workflow = await planner.plan_from_template(template, task_input)
```

### Parallel Execution

```python
# Workflow steps ที่ไม่มี dependencies จะรันแบบ parallel อัตโนมัติ
workflow = {
    "steps": [
        {"step_id": "step1", "depends_on": []},
        {"step_id": "step2", "depends_on": []},  # รันพร้อม step1
        {"step_id": "step3", "depends_on": ["step1", "step2"]}  # รันหลังจาก step1, step2 เสร็จ
    ]
}
```

---

## 📈 การติดตามและ Monitoring

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
# เปิด Grafana dashboard
# URL: http://localhost:3000
# Default credentials: admin/admin
```

### Logs

```bash
# ดู logs
tail -f logs/orchestrator.log

# หรือ Docker logs
docker-compose logs -f orchestrator
```

---

## 🔧 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. API Server ไม่เริ่มทำงาน

**ปัญหา:** Port 8000 ถูกใช้งานแล้ว

**แก้ไข:**
```bash
# ตรวจสอบ process ที่ใช้ port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# หรือเปลี่ยน port ใน .env
API_PORT=8001
```

#### 2. Redis Connection Error

**ปัญหา:** ไม่สามารถเชื่อมต่อ Redis ได้

**แก้ไข:**
```bash
# ตรวจสอบว่า Redis ทำงานอยู่
docker ps | grep redis

# เริ่ม Redis
docker-compose -f docker-compose.dev.yml up -d redis

# ทดสอบ connection
docker exec orchestrator-ai-redis-1 redis-cli ping
```

#### 3. Database Connection Error

**ปัญหา:** ไม่สามารถเชื่อมต่อ PostgreSQL ได้

**แก้ไข:**
```bash
# ตรวจสอบ PostgreSQL
docker ps | grep postgres

# เริ่ม PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# ทดสอบ connection
docker exec orchestrator-ai-postgres-1 pg_isready -U orchestrator
```

#### 4. LLM API Key ไม่ทำงาน

**ปัญหา:** Agents ไม่สามารถเรียกใช้ LLM ได้

**แก้ไข:**
```bash
# ตรวจสอบ API key ใน .env
cat .env | grep API_KEY

# ตรวจสอบว่า package ติดตั้งแล้ว
pip list | grep -E "openai|anthropic|google-generativeai"

# ติดตั้ง package ที่ขาด
pip install google-generativeai anthropic openai
```

#### 5. Import Errors

**ปัญหา:** Module not found errors

**แก้ไข:**
```bash
# ตรวจสอบ virtual environment
which python  # ควรชี้ไปที่ venv/bin/python

# เปิดใช้งาน virtual environment
source venv/bin/activate

# ติดตั้ง dependencies ใหม่
pip install -r requirements.txt
```

---

## 💡 ตัวอย่างการใช้งาน

### ตัวอย่าง 1: Simple Echo Task

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

### ตัวอย่าง 2: Multi-Step Workflow

```python
task = {
    "type": "research_and_analyze",
    "input": {
        "query": "AI trends 2024",
        "analysis_type": "trend"
    }
}

# Orchestrator จะ:
# 1. ใช้ ResearchAgent เพื่อค้นหาข้อมูล
# 2. ใช้ AnalysisAgent เพื่อวิเคราะห์ผลลัพธ์
# 3. ส่งคืนผลลัพธ์ที่สรุปแล้ว
result = await orchestrator.execute(task)
```

### ตัวอย่าง 3: API Call with Callback

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

### ตัวอย่าง 4: CLI Usage

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

## 📚 เอกสารเพิ่มเติม

- [Architecture Documentation](ARCHITECTURE.md)
- [Development Guide](../development/README_DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/docs) (เมื่อ server ทำงาน)
- [Code Review](CODE_REVIEW.md)
- [Test Results](../testing/TEST_RESULTS.md)

---

## 🆘 การขอความช่วยเหลือ

1. ตรวจสอบ [Troubleshooting](#การแก้ไขปัญหา)
2. ดู [API Documentation](http://localhost:8000/docs)
3. ตรวจสอบ logs สำหรับ error messages
4. ดู [GitHub Issues](repository-url/issues)

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

