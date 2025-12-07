# สถาปัตยกรรมระบบ Orchestrator AI Agent

## ภาพรวมสถาปัตยกรรม (Architecture Overview)

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│              (Web UI, API Clients, CLI)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│            (Authentication, Rate Limiting)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Engine                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Task Planner │  │ Agent Select │  │ Workflow Exec│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Message     │ │  Agent       │ │  State       │
│  Broker      │ │  Registry    │ │  Store       │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI Agents                               │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │ Agent 1│  │ Agent 2│  │ Agent 3│  │ Agent N│  ...      │
│  └────────┘  └────────┘  └────────┘  └────────┘           │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              External Services & Resources                   │
│  (APIs, Databases, File Systems, LLM Services)              │
└─────────────────────────────────────────────────────────────┘
```

## Components Breakdown

### 1. Orchestrator Engine

#### 1.1 Task Planner
- **หน้าที่**: วิเคราะห์และแยกย่อยงาน
- **Input**: User request/task
- **Output**: Task graph/workflow plan
- **Capabilities**:
  - Task decomposition
  - Dependency analysis
  - Resource requirement estimation
  - Optimization strategies

#### 1.2 Agent Selector
- **หน้าที่**: เลือก agents ที่เหมาะสม
- **Input**: Task requirements
- **Output**: Selected agents list
- **Capabilities**:
  - Agent capability matching
  - Load balancing
  - Cost optimization
  - Quality scoring

#### 1.3 Workflow Executor
- **หน้าที่**: ควบคุมการทำงานของ workflow
- **Input**: Workflow plan
- **Output**: Execution results
- **Capabilities**:
  - Sequential execution
  - Parallel execution
  - Conditional routing
  - Error handling
  - Retry logic

### 2. Agent Registry

```
Agent Registry Structure:
{
  "agent_id": "unique_id",
  "name": "Agent Name",
  "capabilities": ["capability1", "capability2"],
  "status": "active|inactive|busy",
  "metadata": {
    "version": "1.0.0",
    "description": "...",
    "max_concurrent_tasks": 5,
    "rate_limit": 100,
    "cost_per_request": 0.01
  },
  "health": {
    "last_heartbeat": "timestamp",
    "success_rate": 0.95,
    "avg_latency": 150
  }
}
```

### 3. Message Broker

#### Message Types:
1. **Task Messages**: งานที่ต้องทำ
2. **Response Messages**: ผลลัพธ์จาก agent
3. **Status Messages**: สถานะของ agent
4. **Event Messages**: Events ที่เกิดขึ้น

#### Message Format:
```json
{
  "message_id": "uuid",
  "type": "task|response|status|event",
  "from": "agent_id",
  "to": "agent_id|broadcast",
  "timestamp": "iso_datetime",
  "payload": {},
  "correlation_id": "uuid"
}
```

### 4. State Store

#### State Structure:
```json
{
  "workflow_id": "uuid",
  "state": {
    "current_step": 3,
    "variables": {},
    "results": {},
    "metadata": {}
  },
  "version": 1,
  "timestamp": "iso_datetime"
}
```

## Data Flow

### Typical Workflow Execution:

1. **Task Submission**
   ```
   Client → API Gateway → Orchestrator Engine
   ```

2. **Planning Phase**
   ```
   Orchestrator → Task Planner
   Task Planner → Decompose Task
   Task Planner → Create Workflow Graph
   ```

3. **Agent Selection**
   ```
   Orchestrator → Agent Selector
   Agent Selector → Query Agent Registry
   Agent Selector → Select Best Agents
   ```

4. **Execution Phase**
   ```
   Orchestrator → Workflow Executor
   Workflow Executor → Message Broker
   Message Broker → Agents
   ```

5. **State Management**
   ```
   Agents → Update State Store
   Workflow Executor → Read State Store
   ```

6. **Result Aggregation**
   ```
   Agents → Response Messages
   Message Broker → Orchestrator
   Orchestrator → Aggregate Results
   Orchestrator → Client
   ```

## Agent Communication Patterns

### Pattern 1: Request-Response
```
Orchestrator → [Request] → Agent
Agent → [Response] → Orchestrator
```

### Pattern 2: Event-Driven
```
Agent 1 → [Event] → Message Broker
Message Broker → [Event] → Agent 2
```

### Pattern 3: Pub-Sub
```
Agent 1 → [Publish] → Topic
Topic → [Subscribe] → Agent 2, Agent 3
```

### Pattern 4: Workflow Chain
```
Orchestrator → Agent A → Agent B → Agent C → Orchestrator
```

## Scalability Architecture

### Horizontal Scaling:

```
                    ┌─────────────┐
                    │ Load        │
                    │ Balancer    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │Orch.    │       │Orch.    │       │Orch.    │
   │Instance │       │Instance │       │Instance │
   │   1     │       │   2     │       │   N     │
   └────┬────┘       └────┬────┘       └────┬────┘
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Shared      │
                    │ Resources   │
                    │ (Redis, DB) │
                    └─────────────┘
```

## Database Schema

### Workflows Table
```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    workflow_graph JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id),
    agent_id UUID REFERENCES agents(id),
    task_type VARCHAR(100),
    status VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Agents Table
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    capabilities TEXT[],
    endpoint VARCHAR(255),
    status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### State Snapshots Table
```sql
CREATE TABLE state_snapshots (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id),
    state_data JSONB,
    version INTEGER,
    created_at TIMESTAMP
);
```

## Security Architecture

### Authentication Flow:
```
Client → API Key/Token → API Gateway
API Gateway → Validate → Orchestrator
```

### Authorization:
- Role-Based Access Control (RBAC)
- Agent-level permissions
- Resource-level permissions

### Data Encryption:
- TLS/SSL for data in transit
- AES-256 for data at rest
- Encrypted message payloads

## Monitoring Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  ┌──────────┐  ┌──────────┐           │
│  │ Metrics  │  │  Logs    │           │
│  └────┬─────┘  └────┬─────┘           │
└───────┼──────────────┼─────────────────┘
        │              │
        ▼              ▼
┌─────────────────────────────────────────┐
│      Collection Layer                   │
│  ┌──────────┐  ┌──────────┐           │
│  │Prometheus│  │   ELK    │           │
│  └────┬─────┘  └────┬─────┘           │
└───────┼──────────────┼─────────────────┘
        │              │
        ▼              ▼
┌─────────────────────────────────────────┐
│      Visualization Layer                │
│  ┌──────────┐  ┌──────────┐           │
│  │ Grafana  │  │ Kibana   │           │
│  └──────────┘  └──────────┘           │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Container Structure:
```
orchestrator-ai/
├── orchestrator-service/     # Main orchestrator
├── agent-registry-service/   # Agent management
├── message-broker/           # RabbitMQ/Redis
├── state-store/              # Redis/PostgreSQL
├── monitoring/               # Prometheus, Grafana
└── agents/                   # Individual agents
    ├── research-agent/
    ├── code-agent/
    └── ...
```

### Kubernetes Deployment:
- **Deployments**: สำหรับ stateless services
- **StatefulSets**: สำหรับ stateful services (DB, message queue)
- **Services**: สำหรับ service discovery
- **ConfigMaps**: สำหรับ configuration
- **Secrets**: สำหรับ sensitive data
- **HorizontalPodAutoscaler**: สำหรับ auto-scaling

## Performance Considerations

### Caching Strategy:
- **L1 Cache**: In-memory cache (Redis)
- **L2 Cache**: Application-level cache
- **Cache Invalidation**: TTL-based, event-based

### Async Processing:
- All agent communications are async
- Non-blocking I/O operations
- Background task processing

### Connection Pooling:
- Database connection pools
- HTTP client connection pools
- Message broker connection pools

