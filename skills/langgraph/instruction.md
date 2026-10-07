# LangGraph Architectural Instructions for DeepAgents

This document outlines structural guidelines and best practices for developing, debugging, and running stateful agent graphs with LangGraph.

---

## 1. Core Graph Components

### 1.1 StateGraph Architecture
Every LangGraph application centers around a `StateGraph`:
1. **State Definition**: A schema (usually `TypedDict` or Pydantic `BaseModel`) defining all data channels in the graph.
2. **Nodes**: Python functions (sync or async) or runnables that accept the current state and return state updates.
3. **Edges**: Direct connections between nodes (`builder.add_edge("node_a", "node_b")`).
4. **Conditional Edges**: Dynamic routing based on the state contents (`builder.add_conditional_edges("node_a", routing_function, path_map)`).
5. **Special Sentinels**: `START` (entry point) and `END` (termination).

---

## 2. State Design & Reducer Semantics

### 2.1 State Schema Definition
When defining graph state:
```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'add_messages' appends new messages or updates existing messages by ID
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: int
    user_approved: bool
    context: dict[str, str]
```

### 2.2 Custom Reducers
Default channels overwrite previous values. When maintaining an accumulator, list, or counter, specify a custom reducer:
```python
def append_or_extend(current: list[str], new: list[str] | str) -> list[str]:
    if isinstance(new, str):
        return current + [new]
    return current + new

class PipelineState(TypedDict):
    logs: Annotated[list[str], append_or_extend]
```

---

## 3. Node Implementation Best Practices

### 3.1 Return Dictionaries, Not States
A node must return a `dict` containing only the keys it wants to update:
```python
def generate_summary(state: AgentState) -> dict[str, Any]:
    # Correct: return only updated keys
    summary_text = "..."
    return {"context": {"summary": summary_text}, "current_step": state["current_step"] + 1}
```

### 3.2 Error Handling Inside Nodes
Catch recoverable tool or API errors inside nodes rather than allowing the graph execution to crash. Return informative error messages into the state:
```python
def call_external_service(state: AgentState) -> dict[str, Any]:
    try:
        data = client.fetch()
        return {"data": data}
    except Exception as exc:
        return {"error": f"Service unavailable: {exc}"}
```

---

## 4. Conditional Edges & Routing

### 4.1 Routing Functions
Routing functions inspect state and return a string (or literal) representing the target node:
```python
from typing import Literal
from langgraph.graph import END

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    # Check if the LLM made any tool calls
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END
```

### 4.2 Explicit Path Mapping
Explicitly mapping return values to node names improves clarity and prevents typos:
```python
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools_node",
        END: END,
    }
)
```

---

## 5. Persistence & Checkpointing

### 5.1 Checkpointers
Checkpointers serialize and save the graph state after every superstep:
- **`MemorySaver`**: In-memory ephemeral checkpointer for rapid testing and interactive sessions.
- **`SqliteSaver`**: Local disk persistence via SQLite (`SqliteSaver.from_conn_string("state.db")`).
- **`AsyncSqliteSaver` / PostgresSaver**: Production multi-user persistence.

### 5.2 Thread IDs
Every invocation of a checkpointed graph requires a `thread_id` in the configuration:
```python
config = {"configurable": {"thread_id": "session-user-123"}}
app = builder.compile(checkpointer=checkpointer)
result = app.invoke({"messages": [...]}, config=config)
```

---

## 6. Human-in-the-Loop & Breakpoints

LangGraph supports pausing execution for review before or after critical nodes:
- **Compile-Time Breakpoints**:
  ```python
  app = builder.compile(
      checkpointer=checkpointer,
      interrupt_before=["deploy_node"],  # Pauses before execution of deploy_node
  )
  ```
- **Dynamic Interrupts**:
  ```python
  from langgraph.types import interrupt

  def critical_node(state: AgentState):
      # Pauses and surfaces question to the user
      approval = interrupt({"prompt": "Approve transfer of $500?"})
      if approval == "yes":
          return {"status": "transferred"}
      return {"status": "rejected"}
  ```

---

## 7. DeepAgents Graph Integration

DeepAgents builds upon LangGraph primitives:
- `DeepAgentState` extends message channels with in-memory files and memory snapshots.
- Storage backends (`FilesystemBackend`, `StoreBackend`) decouple file operations from model context.
- `SubAgentMiddleware` coordinates child LangGraph workflows, isolating context and specialized prompts.
- When troubleshooting DeepAgents, inspect graph execution traces, state channels, and recursion limits (default `recursion_limit: 9999`).
