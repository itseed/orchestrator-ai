# Orchestrator AI Agent

ระบบ Orchestrator AI Agent ที่ออกแบบมาเพื่อจัดการและควบคุมการทำงานของ AI agents หลายตัวให้ทำงานร่วมกันอย่างมีประสิทธิภาพ

## คุณสมบัติหลัก (Key Features)

- 🤖 **Multi-Agent Coordination**: ประสานงาน agents หลายตัวให้ทำงานร่วมกัน
- 📋 **Task Orchestration**: จัดการและควบคุม workflow ที่ซับซ้อน
- 🔄 **Parallel & Sequential Execution**: รองรับทั้งการทำงานแบบขนานและแบบลำดับ
- 🎯 **Intelligent Agent Selection**: เลือก agents ที่เหมาะสมอัตโนมัติ
- 📊 **Real-time Monitoring**: ติดตามสถานะแบบ real-time
- 🛡️ **Fault Tolerance**: รองรับข้อผิดพลาดและสามารถกู้คืนได้
- ⚡ **Scalable Architecture**: ขยายระบบได้ง่าย

## โครงสร้างโปรเจกต์ (Project Structure)

```
orchestrator-ai/
├── docs/                      # เอกสาร
│   ├── DESIGN.md             # เอกสารออกแบบระบบ
│   └── ARCHITECTURE.md       # เอกสารสถาปัตยกรรม
├── orchestrator/             # Core orchestrator engine
│   ├── __init__.py
│   ├── engine.py            # Orchestrator engine
│   ├── planner.py           # Task planner
│   ├── selector.py          # Agent selector
│   └── executor.py          # Workflow executor
├── agents/                   # Agent implementations
│   ├── base.py              # Base agent class
│   ├── registry.py          # Agent registry
│   └── specialized/         # Specialized agents
│       ├── research_agent.py
│       ├── code_agent.py
│       └── ...
├── messaging/                # Message broker
│   ├── __init__.py
│   ├── broker.py
│   └── message.py
├── state/                    # State management
│   ├── __init__.py
│   ├── store.py
│   └── snapshot.py
├── api/                      # API layer
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
├── monitoring/               # Monitoring & observability
│   ├── metrics.py
│   ├── logger.py
│   └── dashboard.py
├── config/                   # Configuration
│   └── settings.py
├── tests/                    # Tests
│   ├── unit/
│   └── integration/
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker compose
└── README.md               # This file
```

## ความสามารถของระบบ (System Capabilities)

### 1. Task Management
- แยกย่อยงานที่ซับซ้อนให้เป็นงานย่อย
- วางแผน workflow อัตโนมัติ
- จัดลำดับความสำคัญของงาน

### 2. Agent Management
- จดทะเบียนและค้นหา agents
- เลือก agents ที่เหมาะสม
- ติดตามสถานะและประสิทธิภาพ

### 3. Multi-Agent Coordination
- ประสานงาน agents หลายตัว
- รองรับการทำงานแบบขนาน
- จัดการ dependencies ระหว่าง agents

### 4. Communication
- ระบบส่งข้อความระหว่าง agents
- รองรับหลาย communication patterns
- Event-driven architecture

### 5. State Management
- จัดการ shared state
- Persistence และ versioning
- Conflict resolution

### 6. Error Handling
- Retry mechanisms
- Circuit breaker pattern
- Graceful degradation
- Checkpointing และ recovery

## การติดตั้ง (Installation)

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (สำหรับ production)
- Redis (สำหรับ message broker และ state store)
- PostgreSQL (สำหรับ persistent storage - optional)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd orchestrator-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if using DB)
# Run services
docker-compose up -d
```

## การใช้งาน (Usage)

### Basic Example

```python
from orchestrator import OrchestratorEngine
from agents.registry import AgentRegistry

# Initialize orchestrator
orchestrator = OrchestratorEngine()

# Register agents
registry = AgentRegistry()
registry.register_agent("research_agent", ResearchAgent())
registry.register_agent("analysis_agent", AnalysisAgent())

# Submit task
task = {
    "type": "research_and_analyze",
    "query": "Latest trends in AI",
    "output_format": "report"
}

result = await orchestrator.execute(task)
print(result)
```

### API Usage

```bash
# Start API server
python -m api.main

# Submit task via API
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "research_and_analyze",
    "query": "Latest trends in AI"
  }'

# Check task status
curl http://localhost:8000/api/v1/tasks/{task_id}/status
```

## การพัฒนาต่อ (Development)

### สร้าง Agent ใหม่

1. สร้างคลาสที่สืบทอดจาก `BaseAgent`
2. กำหนด capabilities
3. Implement `execute` method
4. Register agent กับ registry

```python
from agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_custom_agent",
            name="My Custom Agent",
            capabilities=["custom_task"]
        )
    
    async def execute(self, task: dict) -> dict:
        # Your implementation here
        result = await self.process_task(task)
        return {"status": "success", "result": result}
```

## Architecture Overview

ดูเอกสารเพิ่มเติมได้ที่:
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - **แผนการพัฒนาแบบละเอียด** ⭐
- [.context/DESIGN.md](.context/DESIGN.md) - เอกสารออกแบบระบบ
- [.context/ARCHITECTURE.md](.context/ARCHITECTURE.md) - เอกสารสถาปัตยกรรม
- [.context/WORKFLOW_EXAMPLES.md](.context/WORKFLOW_EXAMPLES.md) - ตัวอย่าง workflow
- [.context/QUICK_START.md](.context/QUICK_START.md) - Quick Start Guide

## การทดสอบ (Testing)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orchestrator --cov=agents

# Run specific test
pytest tests/unit/test_orchestrator.py
```

## Monitoring

เข้าใช้ dashboard:
- Metrics Dashboard: http://localhost:3000 (Grafana)
- API Documentation: http://localhost:8000/docs

## License

MIT License

## Contributing

ยินดีต้อนรับ contribution! กรุณาอ่าน CONTRIBUTING.md ก่อน

## Roadmap

- [ ] Phase 1: Core Orchestrator Engine (4-6 สัปดาห์)
- [ ] Phase 2: Multi-Agent Support (6-8 สัปดาห์)
- [ ] Phase 3: Advanced Features (4-6 สัปดาห์)
- [ ] Phase 4: Production Ready (4-6 สัปดาห์)

**ดูแผนการพัฒนาแบบละเอียด**: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

