# Quick Start Guide

## ภาพรวมระบบ (System Overview)

Orchestrator AI Agent เป็นระบบที่:
- 🎯 **จัดสรรงาน** ให้กับ AI agents ที่เหมาะสม
- 🔄 **ประสานงาน** agents หลายตัวให้ทำงานร่วมกัน
- 📊 **ติดตามและควบคุม** workflow ที่ซับซ้อน
- ⚡ **รองรับการทำงานแบบขนาน** เพื่อเพิ่มประสิทธิภาพ

## ความสามารถหลัก (Key Capabilities)

### ✅ Task Orchestration
- แยกย่อยงานที่ซับซ้อน
- วางแผน workflow อัตโนมัติ
- จัดลำดับความสำคัญ

### ✅ Multi-Agent Coordination
- จัดการ agents หลายตัวพร้อมกัน
- ประสานงานการสื่อสารระหว่าง agents
- รองรับการทำงานแบบขนานและแบบลำดับ

### ✅ Intelligent Agent Selection
- เลือก agents ที่เหมาะสมอัตโนมัติ
- จัดการ workload
- ประเมินประสิทธิภาพ

### ✅ Fault Tolerance
- Retry mechanisms
- Error recovery
- Graceful degradation

## ตัวอย่างการใช้งาน (Usage Examples)

### 1. Simple Task

```python
from orchestrator import OrchestratorEngine

orchestrator = OrchestratorEngine()

task = {
    "type": "research",
    "query": "Latest AI trends"
}

result = await orchestrator.execute(task)
```

### 2. Multi-Agent Workflow

```python
workflow = {
    "name": "research_and_analyze",
    "steps": [
        {
            "agent": "research_agent",
            "action": "search",
            "input": {"query": "AI trends"}
        },
        {
            "agent": "analysis_agent",
            "action": "analyze",
            "input": {"data": "{{previous_step.output}}"},
            "depends_on": ["research_agent"]
        }
    ]
}

result = await orchestrator.execute_workflow(workflow)
```

### 3. Parallel Processing

```python
workflow = {
    "name": "parallel_analysis",
    "parallel": True,
    "steps": [
        {"agent": "text_analyzer", "input": {"data": "text1"}},
        {"agent": "image_analyzer", "input": {"data": "image1"}},
        {"agent": "audio_analyzer", "input": {"data": "audio1"}}
    ],
    "aggregate": {
        "agent": "result_aggregator",
        "input": {"results": "{{all_steps.output}}"}
    }
}
```

## Agent Types

### Specialized Agents
- **Research Agent**: ค้นหาข้อมูล
- **Code Agent**: สร้างและแก้ไขโค้ด
- **Analysis Agent**: วิเคราะห์ข้อมูล
- **Data Processing Agent**: ประมวลผลข้อมูล
- **Validation Agent**: ตรวจสอบผลลัพธ์

### Coordinator Agents
- **Task Coordinator**: ประสานงานงานย่อย
- **Resource Coordinator**: จัดการทรัพยากร
- **Quality Coordinator**: ควบคุมคุณภาพ

## Workflow Patterns

### 1. Sequential
```
Task A → Task B → Task C
```

### 2. Parallel
```
        → Task B →
Task A →           → Task D
        → Task C →
```

### 3. Conditional
```
Task A → [Condition?] → Task B (if true)
                    → Task C (if false)
```

### 4. Loop
```
Task A → [Condition?] → Task A (loop)
                   → Exit
```

## Communication Patterns

### Request-Response
```
Orchestrator → Agent → Response
```

### Event-Driven
```
Agent 1 → Event → Broker → Agent 2
```

### Pub-Sub
```
Publisher → Topic → Subscriber 1
                  → Subscriber 2
```

## เอกสารเพิ่มเติม

- 📖 [DESIGN.md](DESIGN.md) - เอกสารออกแบบระบบ
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - สถาปัตยกรรมระบบ
- 🔄 [WORKFLOW_EXAMPLES.md](WORKFLOW_EXAMPLES.md) - ตัวอย่าง workflow
- 📚 [README.md](README.md) - เอกสารหลัก

## Next Steps

1. อ่าน [DESIGN.md](DESIGN.md) เพื่อเข้าใจระบบ
2. ดู [ARCHITECTURE.md](ARCHITECTURE.md) เพื่อเข้าใจโครงสร้าง
3. ศึกษา [WORKFLOW_EXAMPLES.md](WORKFLOW_EXAMPLES.md) เพื่อดูตัวอย่าง
4. เริ่มพัฒนา agent แรกของคุณ!

