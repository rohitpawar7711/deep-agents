# AGENTS.md — DeepAgents Project Context & Architecture Blueprint

> **Role & Purpose**: This document serves as the persistent memory and operational guideline for DeepAgents instances working within this workspace. When initialized with memory support (`memory=["/projects/Agents.md"]` or via `MemoryMiddleware`), this content is injected into the agent's system prompt to ground reasoning, provide architectural awareness, and define operational conventions.

---

## 1. DeepAgents Architectural Overview

DeepAgents is an agentic framework built on top of **LangChain** and **LangGraph**, engineered for deep, multi-step reasoning, autonomous tool execution, persistent memory management, and subagent orchestration.

```
+-----------------------------------------------------------------------+
|                             Deep Agent                                |
+-----------------------------------------------------------------------+
|  System Prompt + Memory (<agent_memory> from AGENTS.md)               |
+-----------------------------------------------------------------------+
|                            Middleware Stack                           |
|  - MemoryMiddleware (AGENTS.md injection & updates)                   |
|  - FilesystemMiddleware (read_file, write_file, edit_file)            |
|  - SubAgentMiddleware (hierarchical task delegation)                  |
|  - HumanInTheLoopMiddleware (interrupt_on approval hooks)             |
+-----------------------------------------------------------------------+
|                       LangGraph State Engine                          |
|  - DeepAgentState (messages, files, memory_contents, delta reducers)  |
+-----------------------------------------------------------------------+
|                           Backend Layer                               |
|  - StateBackend: In-memory virtual filesystem in graph state          |
|  - FilesystemBackend: Direct disk operations with virtual roots       |
|  - StoreBackend: Persistent cross-thread key-value storage            |
+-----------------------------------------------------------------------+
```

---

## 2. Core Components

### A. Graph Runtime & State (`DeepAgentState`)
- **Execution Engine**: Implemented as a compiled LangGraph state machine (`CompiledStateGraph`).
- **State Schema**: Subclasses `DeepAgentState`, managing:
  - `messages`: Message list reduced via `DeltaChannel` for efficient streaming and history tracking.
  - `files`: In-memory filesystem dictionary tracking paths, contents, timestamps, and encodings.
  - `memory_contents`: Cached memory snapshots mapped from source paths.

### B. Storage Backends (`BackendProtocol`)
DeepAgents decouples file storage and tool operations through interchangeable backends:
1. **`StateBackend` (Default)**:
   - Stores files ephemerally within the agent's graph state dictionary (`state["files"]`).
   - Best for stateless, sandboxed runs where disk writes are unwanted.
2. **`FilesystemBackend`**:
   - Bridges tool calls directly to the local filesystem or virtual root directory (`root_dir`).
   - Supports `virtual_mode` to enforce sandboxed relative path resolution.
3. **`StoreBackend`**:
   - Integrates with `langgraph.store` (e.g., `InMemoryStore` or database-backed stores).
   - Enables persistent memory and file state across distinct thread IDs using configurable namespaces.

### C. Middleware Pipeline
DeepAgents processes model requests and agent lifecycles via layered middleware:
- **`MemoryMiddleware`**: Loads `AGENTS.md` files at startup before agent invocation and injects them into the system prompt inside `<agent_memory>`.
- **`FilesystemMiddleware`**: Supplies built-in filesystem tools (`read_file`, `write_file`, `edit_file`, `list_directory`) and evaluates `FilesystemPermission` rules (`allow`, `deny`, `interrupt`).
- **`SubAgentMiddleware`**: Allows the primary agent to spawn focused, isolated subagents (`SubAgent`, `CompiledSubAgent`) for parallel or complex subtasks.
- **`HumanInTheLoopMiddleware`**: Enables approval interrupts for sensitive tool invocations (configured via `interrupt_on`).

---

## 3. Agent Execution Lifecycle

When invoked, the agent adheres to an iterative ReAct reasoning loop:
1. **Context & Memory Ingestion**: The agent boots, loads memory sources (`Agents.md`), and receives user instructions.
2. **Plan & Decompose**: High-level objectives are decomposed into actionable sub-steps.
3. **Tool Execution**: Tools are called systematically (reading context before modifying files).
4. **Observation & Verification**: Output from tool execution is checked for errors or discrepancies.
5. **Self-Correction & Refinement**: If a tool fails or assumptions prove false, the strategy adapts iteratively.
6. **Synthesis**: The agent delivers a concise, verified final answer.

---

## 4. Usage & Initialization Pattern

To instantiate a DeepAgent with this memory file loaded:

```python
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

load_dotenv()

# Define backend rooted at current workspace
backend = FilesystemBackend(root_dir=".", virtual_mode=True)

# Initialize DeepAgent with memory pointing to this file and registered skills
agent = create_deep_agent(
    model="openai:gpt-5.4",
    backend=backend,
    memory=["/projects/Agents.md"],
    skills=["skills"],
    system_prompt="You are an autonomous engineering agent specialized in deep reasoning."
)

# Invoke the agent
response = agent.invoke({
    "messages": [
        {"role": "user", "content": "Analyze the project structure and summarize the architecture."}
    ]
})
```

---

## 5. Available Agent Skills (`/skills/`)

DeepAgents utilizes progressive disclosure via domain skills located in `/skills/`:
- **`python`** (`/skills/python/SKILL.md`): Modern Python engineering, Pydantic v2, async, testing, and debugging.
- **`langgraph`** (`/skills/langgraph/SKILL.md`): Stateful agent graphs, loops, checkpointers, and multi-agent systems.
- **`docker`** (`/skills/docker/SKILL.md`): Containerization, multi-stage Dockerfiles, Compose orchestration, and security.
- **`report-writing`** (`/skills/report-writing/SKILL.md`): Structured report blueprints, RCA templates, and synthesis.

Each skill contains:
1. `SKILL.md` (or `skill.md`): Spec-compliant metadata frontmatter and high-level overview.
2. `instruction.md`: Procedural guidelines, rules, and best practices.
3. `examples.md`: Practical, runnable code patterns and templates.

---

## 6. Working Memory Guidelines for Agents

- **Read Before Write**: Always inspect existing files using `read_file` before calling `edit_file` or `write_file`.
- **Durable Knowledge Updates**: If the user establishes lasting project preferences, architectural rules, or workflow patterns, record them directly into this `Agents.md` using `edit_file`.
- **Transient Data Exclusion**: Do not store temporary conversation state, one-off queries, or execution logs in memory.
- **Security & Secrets**: Never write API keys, tokens, or credentials into memory files.
