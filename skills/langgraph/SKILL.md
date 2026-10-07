---
name: langgraph
description: Stateful multi-agent graph orchestration, cycles, human-in-the-loop, persistence, and state management using LangGraph. Use whenever designing, constructing, debugging, or optimizing LangGraph workflows, StateGraph, custom reducers, checkpointers, or DeepAgents graph runtime.
license: MIT
compatibility: langgraph >= 0.2.0, langchain >= 0.3.0
allowed-tools: read_file write_file edit_file list_directory
---

# LangGraph Skill (LangGraph / Langraph)

## Overview
This skill equips DeepAgents with comprehensive expertise in **LangGraph**, the stateful agent orchestration framework that powers cyclic, multi-agent, and persistent AI systems. DeepAgents itself is built on top of LangGraph (`CompiledStateGraph`), making this skill central to the agent's internal architecture, execution loop, state channels, and subagent orchestration.

Whether the user asks about building custom agent graphs, implementing human-in-the-loop breakpoints, configuring checkpointers, or understanding how DeepAgents executes under the hood, this skill provides the necessary architectural context and patterns.

---

## When to Use This Skill
- Building stateful conversational agents, multi-agent systems, or autonomous workflows.
- Designing graphs with cyclic loops, tool-calling nodes, and dynamic conditional branching.
- Implementing state management using `TypedDict`, `MessagesState`, and custom reducers (`Annotated`).
- Adding persistence, session resumption, and time-travel with `MemorySaver`, `SqliteSaver`, or `StoreBackend`.
- Implementing human-in-the-loop approvals (`interrupt`, breakpoint before/after nodes).
- Debugging or extending DeepAgents internals (`DeepAgentState`, `FilesystemBackend`, middleware).

---

## Skill Navigation & Progressive Disclosure
For in-depth operational patterns, refer to the companion documents:

1. **[`instruction.md`](./instruction.md)**:
   - Fundamental LangGraph architecture: nodes, edges, channels, and compiled graphs.
   - State design best practices: immutable state transitions, reducer semantics (`add_messages`).
   - Conditional routing logic, entry points, and terminal conditions (`START`, `END`).
   - Persistence strategies: thread-based checkpointers, cross-thread storage (`InMemoryStore`).
   - Human-in-the-loop patterns: pausing execution for human approval and resuming with state updates.
   - DeepAgents integration: how `create_deep_agent` leverages LangGraph state machines.

2. **[`examples.md`](./examples.md)**:
   - Production-ready runnable graph patterns:
     - Minimal Tool-Calling ReAct Graph using `StateGraph` and `ToolNode`.
     - Multi-Agent Supervisor-Worker Architecture with dynamic dispatch.
     - Stateful Chatbot with checkpoint memory across conversation threads.
     - Human-in-the-Loop approval graph with breakpoint interrupts.
     - Multi-step Research & Validation loop with conditional retry edges.

---

## Core Architecture Principles
1. **Nodes as Pure Functions**: Nodes receive the current state and return a dictionary representing the state update, not an entirely mutated state object.
2. **Channel Reducers**: Always use reducer functions (`add_messages` or custom functions) on list channels to prevent state overwriting.
3. **Explicit Graph Boundaries**: Always connect components clearly using `START`, node definitions, explicit edges (`add_edge`), conditional edges (`add_conditional_edges`), and `END`.
4. **Thread-Safe Checkpointing**: Ensure every run with persistent memory passes a configuration dictionary containing a unique `configurable: {"thread_id": "..."}`.
