# ตัวอย่าง Workflow และ Use Cases

## 1. Research & Analysis Workflow

### Use Case: วิจัยและวิเคราะห์หัวข้อ

```
User Request: "Research and analyze the latest AI trends"
    │
    ▼
┌─────────────────────────────────────────┐
│      Orchestrator Engine                │
│  • Decompose task                      │
│  • Plan workflow                       │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Task Decomposition  │
    │  1. Research         │
    │  2. Analyze          │
    │  3. Synthesize       │
    │  4. Format           │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Agent Selection     │
    │  • Research Agent    │
    │  • Analysis Agent    │
    │  • Synthesis Agent   │
    │  • Format Agent      │
    └──────────┬───────────┘
               │
               ▼
┌───────────────────────────────────────────┐
│  Sequential Workflow Execution            │
│                                           │
│  Step 1: Research Agent                   │
│  ┌──────────────────────────────┐        │
│  │ • Search multiple sources    │        │
│  │ • Collect relevant data      │        │
│  │ • Return research findings   │        │
│  └──────────────┬───────────────┘        │
│                 │                        │
│                 ▼                        │
│  Step 2: Analysis Agent                  │
│  ┌──────────────────────────────┐        │
│  │ • Analyze research data      │        │
│  │ • Identify key patterns      │        │
│  │ • Extract insights           │        │
│  └──────────────┬───────────────┘        │
│                 │                        │
│                 ▼                        │
│  Step 3: Synthesis Agent                 │
│  ┌──────────────────────────────┐        │
│  │ • Combine insights           │        │
│  │ • Create coherent narrative  │        │
│  │ • Structure content          │        │
│  └──────────────┬───────────────┘        │
│                 │                        │
│                 ▼                        │
│  Step 4: Format Agent                    │
│  ┌──────────────────────────────┐        │
│  │ • Format to requested type   │        │
│  │ • Add formatting/styling     │        │
│  │ • Final validation           │        │
│  └──────────────┬───────────────┘        │
│                 │                        │
└─────────────────┼────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Final Result  │
         └────────────────┘
```

### Implementation Example

```python
workflow = {
    "name": "research_and_analysis",
    "steps": [
        {
            "step_id": "research",
            "agent": "research_agent",
            "input": {
                "query": "{{user_query}}",
                "sources": ["web", "papers", "news"]
            },
            "output_key": "research_data"
        },
        {
            "step_id": "analyze",
            "agent": "analysis_agent",
            "input": {
                "data": "{{steps.research.output}}"
            },
            "depends_on": ["research"],
            "output_key": "analysis_results"
        },
        {
            "step_id": "synthesize",
            "agent": "synthesis_agent",
            "input": {
                "analysis": "{{steps.analyze.output}}"
            },
            "depends_on": ["analyze"],
            "output_key": "synthesized_content"
        },
        {
            "step_id": "format",
            "agent": "format_agent",
            "input": {
                "content": "{{steps.synthesize.output}}",
                "format": "{{format_type}}"
            },
            "depends_on": ["synthesize"]
        }
    ]
}
```

## 2. Parallel Data Processing Workflow

### Use Case: ประมวลผลข้อมูลหลายแหล่งแบบขนาน

```
User Request: "Process and merge data from 3 sources"
    │
    ▼
┌─────────────────────────────────────────┐
│      Orchestrator Engine                │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Parallel Execution  │
    │                      │
    ├──────────────────────┤
    │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌─────────┐          ┌─────────┐
│Process  │          │Process  │          │Process  │
│Source 1 │          │Source 2 │          │Source 3 │
│Agent    │          │Agent    │          │Agent    │
└────┬────┘          └────┬────┘          └────┬────┘
     │                    │                    │
     └────────────────────┼────────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Aggregation     │
                │  Agent           │
                │  • Merge data    │
                │  • Deduplicate   │
                │  • Normalize     │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Validation      │
                │  Agent           │
                └────────┬─────────┘
                         │
                         ▼
                    Final Result
```

### Implementation Example

```python
workflow = {
    "name": "parallel_data_processing",
    "steps": [
        {
            "step_id": "process_source1",
            "agent": "data_processor_agent",
            "input": {"source": "source1"},
            "parallel": True
        },
        {
            "step_id": "process_source2",
            "agent": "data_processor_agent",
            "input": {"source": "source2"},
            "parallel": True
        },
        {
            "step_id": "process_source3",
            "agent": "data_processor_agent",
            "input": {"source": "source3"},
            "parallel": True
        },
        {
            "step_id": "aggregate",
            "agent": "aggregation_agent",
            "input": {
                "data1": "{{steps.process_source1.output}}",
                "data2": "{{steps.process_source2.output}}",
                "data3": "{{steps.process_source3.output}}"
            },
            "depends_on": ["process_source1", "process_source2", "process_source3"]
        },
        {
            "step_id": "validate",
            "agent": "validation_agent",
            "input": {
                "data": "{{steps.aggregate.output}}"
            },
            "depends_on": ["aggregate"]
        }
    ]
}
```

## 3. Conditional Workflow

### Use Case: Code Generation with Testing

```
User Request: "Generate code and test it"
    │
    ▼
┌─────────────────────────────────────────┐
│      Orchestrator Engine                │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Code Generator      │
    │  Agent               │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Code Validator      │
    │  Agent               │
    └──────────┬───────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌────────┐   ┌────────┐
   │ Valid? │   │Invalid?│
   │  Yes   │   │   No   │
   └───┬────┘   └────┬───┘
       │             │
       │             └──────────────┐
       │                            │
       ▼                            ▼
┌──────────────┐           ┌──────────────┐
│ Test         │           │ Error        │
│ Generator    │           │ Handler      │
│ Agent        │           │ Agent        │
└──────┬───────┘           └──────┬───────┘
       │                          │
       ▼                          │
┌──────────────┐                  │
│ Test         │                  │
│ Executor     │                  │
│ Agent        │                  │
└──────┬───────┘                  │
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
            Final Result
```

### Implementation Example

```python
workflow = {
    "name": "code_generation_with_testing",
    "steps": [
        {
            "step_id": "generate_code",
            "agent": "code_generator_agent",
            "input": {
                "specification": "{{user_spec}}"
            },
            "output_key": "generated_code"
        },
        {
            "step_id": "validate_code",
            "agent": "code_validator_agent",
            "input": {
                "code": "{{steps.generate_code.output}}"
            },
            "depends_on": ["generate_code"],
            "output_key": "validation_result"
        },
        {
            "step_id": "generate_tests",
            "agent": "test_generator_agent",
            "input": {
                "code": "{{steps.generate_code.output}}"
            },
            "depends_on": ["validate_code"],
            "condition": {
                "field": "{{steps.validate_code.output.valid}}",
                "operator": "equals",
                "value": True
            }
        },
        {
            "step_id": "handle_error",
            "agent": "error_handler_agent",
            "input": {
                "error": "{{steps.validate_code.output.error}}"
            },
            "depends_on": ["validate_code"],
            "condition": {
                "field": "{{steps.validate_code.output.valid}}",
                "operator": "equals",
                "value": False
            }
        },
        {
            "step_id": "execute_tests",
            "agent": "test_executor_agent",
            "input": {
                "code": "{{steps.generate_code.output}}",
                "tests": "{{steps.generate_tests.output}}"
            },
            "depends_on": ["generate_tests"]
        }
    ]
}
```

## 4. Fan-out/Fan-in Pattern

### Use Case: วิเคราะห์ข้อมูลหลายประเภทพร้อมกัน

```
User Request: "Analyze text, image, and audio data"
    │
    ▼
┌─────────────────────────────────────────┐
│      Orchestrator Engine                │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Data Splitter       │
    │  Agent               │
    └──────────┬───────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│Text    │ │Image   │ │Audio   │
│Analysis│ │Analysis│ │Analysis│
│Agent   │ │Agent   │ │Agent   │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Result Aggregator   │
    │  Agent               │
    │  • Combine results   │
    │  • Cross-reference   │
    │  • Generate summary  │
    └──────────┬───────────┘
               │
               ▼
          Final Report
```

## 5. Loop Pattern

### Use Case: Iterative Improvement

```
User Request: "Improve code until it passes all tests"
    │
    ▼
┌─────────────────────────────────────────┐
│      Orchestrator Engine                │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │   Loop Start │
        └──────┬───────┘
               │
               ▼
    ┌──────────────────────┐
    │  Code Generator      │
    │  Agent               │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Test Executor       │
    │  Agent               │
    └──────────┬───────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌────────┐   ┌────────┐
   │All     │   │Some    │
   │Pass?   │   │Fail?   │
   └───┬────┘   └────┬───┘
       │             │
       │             │
       ▼             │
  ┌─────────┐        │
  │ Exit    │        │
  │ Loop    │        │
  └─────────┘        │
                     │
                     ▼
            ┌────────────────┐
            │  Code          │
            │  Improver      │
            │  Agent         │
            └────────┬───────┘
                     │
                     │ (Loop back)
                     │
                     └───────┐
                             │
                             │
```

## Agent Communication Examples

### Example 1: Direct Request-Response

```python
# Agent A requests help from Agent B
message = {
    "type": "request",
    "from": "agent_a",
    "to": "agent_b",
    "payload": {
        "action": "translate",
        "text": "Hello World",
        "target_language": "th"
    }
}

# Agent B responds
response = {
    "type": "response",
    "from": "agent_b",
    "to": "agent_a",
    "correlation_id": message["message_id"],
    "payload": {
        "status": "success",
        "translated_text": "สวัสดีชาวโลก"
    }
}
```

### Example 2: Event Broadcasting

```python
# Agent publishes event
event = {
    "type": "event",
    "from": "data_processor_agent",
    "to": "broadcast",
    "event_type": "data_ready",
    "payload": {
        "dataset_id": "dataset_123",
        "record_count": 1000,
        "status": "processed"
    }
}

# Multiple agents can subscribe to this event
# - Notification Agent: Send notification
# - Analytics Agent: Update metrics
# - Storage Agent: Trigger backup
```

### Example 3: Workflow Chain

```python
# Step-by-step message flow
workflow_chain = [
    {
        "step": 1,
        "from": "orchestrator",
        "to": "research_agent",
        "message": "Research topic X"
    },
    {
        "step": 2,
        "from": "research_agent",
        "to": "analysis_agent",
        "message": "Analyze research data",
        "data": "<research_results>"
    },
    {
        "step": 3,
        "from": "analysis_agent",
        "to": "synthesis_agent",
        "message": "Synthesize insights",
        "data": "<analysis_results>"
    },
    {
        "step": 4,
        "from": "synthesis_agent",
        "to": "orchestrator",
        "message": "Final report ready",
        "data": "<final_report>"
    }
]
```

## Error Handling Patterns

### Pattern 1: Retry with Exponential Backoff

```python
error_handling = {
    "retry_policy": {
        "max_retries": 3,
        "backoff_strategy": "exponential",
        "initial_delay": 1,  # seconds
        "max_delay": 60,     # seconds
        "retryable_errors": ["timeout", "network_error", "rate_limit"]
    }
}
```

### Pattern 2: Circuit Breaker

```python
circuit_breaker = {
    "failure_threshold": 5,
    "timeout": 60,  # seconds
    "half_open_max_calls": 3,
    "states": ["closed", "open", "half_open"]
}
```

### Pattern 3: Fallback Agent

```python
fallback_strategy = {
    "primary_agent": "research_agent_v1",
    "fallback_agent": "research_agent_v2",
    "fallback_conditions": [
        "timeout",
        "error_rate > 50%",
        "unavailable"
    ]
}
```

## Performance Optimization Patterns

### Pattern 1: Caching

```python
cache_strategy = {
    "enabled": True,
    "ttl": 3600,  # seconds
    "cache_keys": [
        "research_results",
        "analysis_results"
    ],
    "cache_invalidation": "event_based"
}
```

### Pattern 2: Batch Processing

```python
batch_processing = {
    "enabled": True,
    "batch_size": 10,
    "batch_timeout": 5,  # seconds
    "agents": ["data_processor_agent"]
}
```

### Pattern 3: Async Execution

```python
async_execution = {
    "mode": "async",
    "concurrent_tasks": 5,
    "timeout": 300  # seconds
}
```

