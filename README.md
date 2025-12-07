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
│   ├── ARCHITECTURE.md       # เอกสารสถาปัตยกรรม
│   ├── DEVELOPMENT_PLAN.md   # แผนการพัฒนาแบบละเอียด
│   ├── WORKFLOW_EXAMPLES.md  # ตัวอย่าง workflow
│   └── QUICK_START.md        # Quick Start Guide
├── orchestrator/             # Core orchestrator engine
│   ├── __init__.py
│   ├── engine.py            # Orchestrator engine ✅
│   ├── planner.py           # Task planner ✅
│   ├── selector.py          # Agent selector ✅
│   ├── executor.py          # Workflow executor ✅
│   ├── templates.py         # Workflow templates ✅
│   ├── resource_estimator.py # Resource estimation ✅
│   ├── workflow_chain.py    # Workflow chaining ✅
│   ├── retry.py             # Retry mechanisms ✅
│   ├── circuit_breaker.py   # Circuit breaker ✅
│   ├── degradation.py       # Graceful degradation ✅
│   ├── recovery.py          # Workflow recovery ✅
│   ├── cache.py             # Caching strategy ✅
│   ├── connection_pool.py   # Connection pooling ✅
│   └── async_optimizer.py   # Async optimization ✅
├── agents/                   # Agent implementations
│   ├── __init__.py
│   ├── base.py              # Base agent class ✅
│   ├── registry.py          # Agent registry ✅
│   ├── communication.py     # Agent communication ✅
│   └── specialized/         # Specialized agents
│       ├── __init__.py
│       ├── echo_agent.py    # Echo agent for testing ✅
│       ├── code_agent.py    # Code generation agent ✅
│       ├── research_agent.py # Research agent ✅
│       └── analysis_agent.py # Analysis agent ✅
├── messaging/                # Message broker
│   ├── __init__.py
│   ├── broker.py            # Message broker ✅
│   └── message.py           # Message protocol ✅
├── state/                    # State management
│   ├── __init__.py
│   ├── store.py             # State store ✅
│   ├── redis_store.py       # Redis state store ✅
│   └── snapshot.py          # State snapshots ✅
├── api/                      # API layer
│   ├── __init__.py
│   ├── main.py              # FastAPI app ✅
│   ├── routes.py            # API routes ✅
│   └── models.py            # API models ✅
├── monitoring/               # Monitoring & observability
│   ├── __init__.py
│   ├── logger.py            # Structured logging ✅
│   ├── metrics.py           # Prometheus metrics ✅
│   ├── health.py            # Health checks ✅
│   ├── tracing.py           # Distributed tracing ✅
│   └── dashboard.py         # Monitoring dashboard ✅
├── security/                 # Security & authentication
│   ├── __init__.py
│   ├── auth.py             # Authentication (API Key, JWT) ✅
│   ├── authorization.py    # RBAC & permissions ✅
│   ├── rate_limit.py       # Rate limiting ✅
│   ├── validation.py       # Input/output validation ✅
│   └── encryption.py       # Data encryption ✅
├── database/                 # Database & persistence
│   ├── __init__.py
│   ├── base.py             # Database base & connection ✅
│   ├── models.py           # SQLAlchemy models ✅
│   ├── repositories.py     # Data access layer ✅
│   └── query_optimizer.py  # Query optimization ✅
├── alembic/                  # Database migrations
│   ├── env.py              # Alembic environment ✅
│   └── script.py.mako      # Migration template ✅
├── config/                   # Configuration
│   ├── __init__.py
│   └── settings.py          # Settings management ✅
├── cli/                      # CLI tools
│   ├── __init__.py
│   ├── main.py              # CLI main with Click ✅
│   └── client.py            # API client ✅
├── tests/                    # Tests
│   ├── __init__.py
│   ├── unit/                # Unit tests
│   │   ├── test_base_agent.py ✅
│   │   └── test_registry.py ✅
│   └── integration/         # Integration tests (pending)
├── requirements.txt          # Python dependencies ✅
├── Dockerfile               # Docker configuration ✅
├── docker-compose.yml       # Docker compose ✅
├── main.py                  # Application entry point ✅
└── README.md               # This file
```

**Legend**: ✅ = Completed | (pending) = To be implemented

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
from orchestrator import TaskPlanner
from agents.registry import AgentRegistry
from agents.specialized import EchoAgent

# Initialize components
planner = TaskPlanner()
registry = AgentRegistry()

# Register agents
echo_agent = EchoAgent()
registry.register(echo_agent)

# Create a task
task = {
    "type": "simple",
    "input": {"message": "Hello, World!"}
}

# Plan workflow
workflow = await planner.plan(task)

# Execute via orchestrator engine
from orchestrator.engine import OrchestratorEngine
from state.store import StateStore

orchestrator = OrchestratorEngine()
result = await orchestrator.execute(task)
```

### Current Implementation Status

ระบบปัจจุบันรองรับ:
- ✅ Configuration Management
- ✅ Structured Logging
- ✅ Agent Registration & Discovery
- ✅ Task Planning & Workflow Decomposition
- ✅ Resource Estimation
- ✅ Agent Selection (Core, Load Balancing, Cost Optimization)
- ✅ Workflow Executor (Sequential & Parallel Execution)
- ✅ State Management (In-Memory & Redis-based with Snapshots)
- ✅ Orchestrator Engine (Complete Integration)
- ✅ REST API (Basic: POST/GET Tasks)
- ✅ Message Broker (Redis-based with Request-Response, Pub-Sub, Event-Driven)
- ✅ Parallel Execution (Fan-out/Fan-in, Conditional Routing)
- ✅ Agent Communication (Direct, Mediated, Broadcast)
- ✅ Workflow Chaining & Pipeline Support
- ✅ Error Recovery & Resilience (Retry, Circuit Breaker, Fallback, Recovery)
- ✅ Monitoring & Observability (Prometheus Metrics, Tracing, Health Checks, Dashboard)
- ✅ Performance Optimization (Caching, Connection Pooling, Async Optimization)

**Phase 1, 2 & Phase 3 (Week 15-19): Core Orchestrator, Multi-Agent Support, Error Recovery, Monitoring & Performance - เสร็จสมบูรณ์แล้ว!** 🎉

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
- [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) - **แผนการพัฒนาแบบละเอียด** ⭐
- [docs/DESIGN.md](docs/DESIGN.md) - เอกสารออกแบบระบบ
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - เอกสารสถาปัตยกรรม
- [docs/WORKFLOW_EXAMPLES.md](docs/WORKFLOW_EXAMPLES.md) - ตัวอย่าง workflow
- [docs/QUICK_START.md](docs/QUICK_START.md) - Quick Start Guide

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

### Phase 1: Core Orchestrator Engine (4-6 สัปดาห์) - ✅ Complete

- [x] **Week 1**: Project Setup & Foundation ✅
  - [x] Project structure setup
  - [x] Configuration management
  - [x] Logging system
  
- [x] **Week 2**: Base Agent & Registry ✅
  - [x] BaseAgent abstract class
  - [x] AgentRegistry implementation
  - [x] EchoAgent for testing
  - [x] Unit tests
  
- [x] **Week 3**: Task Planner ✅
  - [x] WorkflowGraph & WorkflowStep
  - [x] Task decomposition
  - [x] Workflow templates
  - [x] Resource estimation
  
- [x] **Week 4**: Agent Selector ✅
  - [x] AgentSelector core
  - [x] Capability matching
  - [x] Agent scoring algorithm
  - [x] Load balancing
  - [x] Cost optimization
  
- [x] **Week 5**: Workflow Executor ✅
  - [x] Sequential execution
  - [x] Error handling
  - [x] State management (basic)
  
- [x] **Week 6**: Orchestrator Engine & API ✅
  - [x] OrchestratorEngine integration
  - [x] REST API (POST/GET tasks)
  - [x] Task lifecycle management

### Phase 2: Multi-Agent Support (6-8 สัปดาห์) - ✅ Complete

- [x] **Week 7-8**: Message Broker & Communication ✅
  - [x] Redis-based MessageBroker
  - [x] Message Protocol (Task, Response, Status, Event)
  - [x] Request-Response pattern
  - [x] Event-Driven pattern
  - [x] Pub-Sub pattern
  
- [x] **Week 9-10**: Parallel Execution ✅
  - [x] Parallel workflow support
  - [x] Fan-out/Fan-in patterns
  - [x] Conditional routing & branching
  
- [x] **Week 11-12**: State Management ✅
  - [x] Redis-based state store
  - [x] Distributed locking
  - [x] State snapshots & recovery
  
- [x] **Week 13-14**: Agent Communication ✅
  - [x] Agent-to-Agent communication
  - [x] Workflow chaining
  - [x] Event system

### Phase 3: Advanced Features (4-6 สัปดาห์) - ✅ Complete

- [x] **Week 15-16**: Error Recovery & Resilience ✅
  - [x] Retry mechanisms (Exponential backoff, multiple strategies)
  - [x] Circuit breaker pattern
  - [x] Graceful degradation & fallback
  - [x] Checkpointing & recovery automation
  
- [x] **Week 17-18**: Monitoring & Observability ✅
  - [x] Metrics collection (Prometheus integration)
  - [x] Enhanced logging & distributed tracing
  - [x] Health checks (System, Agents, State Store, Message Broker)
  - [x] Dashboard (basic web dashboard with real-time updates)
  
- [x] **Week 19**: Performance Optimization ✅
  - [x] Caching strategy (TTL, LRU, Event-based, Manual)
  - [x] Connection pooling (HTTP connection pools)
  - [x] Async optimization (Batch processing, Semaphore control, Lazy loading)

### Phase 4: Production Ready (4-6 สัปดาห์) - 🚧 In Progress

- [x] **Week 20-21**: Security & Authentication ✅
  - [x] Authentication (API Key, JWT)
  - [x] Authorization (RBAC, Permissions)
  - [x] Security Hardening (Input validation, Output sanitization, Rate limiting)
  - [x] Data Encryption (At rest, Message encryption)
  
- [x] **Week 22-23**: Database & Persistence ✅
  - [x] Database setup (PostgreSQL with connection pooling)
  - [x] Data models (Tasks, Workflows, Agents, Snapshots)
  - [x] Data access layer (Repositories, Query optimization)
  - [x] Alembic migrations
  
- [x] **Week 24-25**: CLI Tool ✅
  - [x] CLI framework (Click-based)
  - [x] CLI commands (submit, status, result, list, cancel, generate, health)
  - [x] CLI client (API client with error handling and output formatting)
  
- [x] **Week 26**: Specialized Agents ✅
  - [x] Code generation agent (LLM integration, project analysis, multi-language)
  - [x] Research agent (Web search, academic search, citation handling)
  - [x] Analysis agent (Statistical, pattern, trend analysis, insights)
  
- [ ] **Week 27-28**: Docker & Deployment
  - [ ] Docker optimization
  - [ ] Kubernetes deployment

**ดูแผนการพัฒนาแบบละเอียด**: [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

### ความคืบหน้าล่าสุด

**Last Updated**: 2024-12-07

- ✅ **Phase 1 Complete**: Week 1-6 เสร็จสมบูรณ์แล้ว!
  - ✅ Week 1-3: Foundation & Core Components
  - ✅ Week 4: Agent Selector (Core, Load Balancing, Cost Optimization)
  - ✅ Week 5: Workflow Executor & State Management
  - ✅ Week 6: Orchestrator Engine & REST API

- ✅ **Phase 2 Complete**: Week 7-14 เสร็จสมบูรณ์แล้ว! 🎉
  - ✅ Week 7-8: Message Broker & Communication (Redis-based, Request-Response, Pub-Sub, Events)
  - ✅ Week 9-10: Parallel Execution (Parallel workflows, Fan-out/Fan-in, Conditional routing)
  - ✅ Week 11-12: State Management (Redis store, Distributed locking, Snapshots)
  - ✅ Week 13-14: Agent Communication (Agent-to-agent, Workflow chaining, Event system)

- ✅ **Phase 3 (Week 15-19) Complete**: Error Recovery & Resilience + Monitoring & Observability + Performance Optimization เสร็จสมบูรณ์แล้ว! 🎉
  - ✅ Week 15-16: Error Recovery & Resilience (Retry mechanisms, Circuit breaker, Graceful degradation, Recovery automation)
  - ✅ Week 17-18: Monitoring & Observability (Prometheus metrics, Distributed tracing, Health checks, Dashboard)
  - ✅ Week 19: Performance Optimization (Caching, Connection pooling, Async optimization)

- ✅ **Phase 4 (Week 20-26) Progress**: Security & Authentication + Database & Persistence + CLI Tool + Specialized Agents เสร็จสมบูรณ์แล้ว! 🎉
  - ✅ Week 20-21: Security & Authentication (API Key/JWT, RBAC, Rate limiting, Validation, Encryption)
  - ✅ Week 22-23: Database & Persistence (PostgreSQL, SQLAlchemy models, Repositories, Query optimization, Alembic)
  - ✅ Week 24-25: CLI Tool (Click framework, All commands, API client with formatting)
  - ✅ Week 26: Specialized Agents (Code Generation, Research, Analysis agents with LLM integration)

- 🎯 **Next**: Phase 4 Week 27-28 - Docker & Deployment
- 📦 Latest Commit: `ae225ea` - Phase 4 Week 26: Specialized Agents - Complete

