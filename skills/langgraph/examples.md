# LangGraph Code Examples for DeepAgents

This file provides production-tested, executable patterns demonstrating key LangGraph architectures.

---

## Example 1: Minimal ReAct Tool-Calling Agent with `ToolNode`

```python
"""Basic ReAct agent using StateGraph, ToolNode, and conditional loop edges."""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


# 1. State Definition
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# 2. Tools
@tool
def search_docs(query: str) -> str:
    """Searches official documentation for a given query."""
    return f"Found documentation results for: '{query}'. LangGraph provides cyclic orchestration."


tools = [search_docs]
tool_node = ToolNode(tools)

# 3. Model Binding
model = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)


def call_model(state: State) -> dict[str, list[BaseMessage]]:
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def route_tools(state: State) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# 4. Graph Construction
builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_tools, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")  # Cycle back to agent after tools

graph = builder.compile()

# Example Invocation:
# response = graph.invoke({"messages": [HumanMessage(content="Search docs for cyclic graphs")]})
```

---

## Example 2: Stateful Chatbot with Persistent `MemorySaver`

```python
"""Stateful conversation thread with persistent checkpointer memory across invocations."""

from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


def chatbot_node(state: ChatState) -> dict[str, list[BaseMessage]]:
    reply = llm.invoke(state["messages"])
    return {"messages": [reply]}


builder = StateGraph(ChatState)
builder.add_node("chatbot", chatbot_node)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

checkpointer = MemorySaver()
app = builder.compile(checkpointer=checkpointer)

# Using a persistent thread
thread_config = {"configurable": {"thread_id": "conversation-user-001"}}

# Turn 1
turn_1 = app.invoke(
    {"messages": [HumanMessage(content="Hello! My name is Alice.")]},
    config=thread_config,
)

# Turn 2 (Remembers name from thread state)
turn_2 = app.invoke(
    {"messages": [HumanMessage(content="What is my name?")]},
    config=thread_config,
)
```

---

## Example 3: Supervisor-Worker Multi-Agent Orchestration

```python
"""Supervisor pattern delegating tasks to specialized worker nodes and synthesizing output."""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class TeamState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_worker: str
    task_result: str


class RouterDecision(BaseModel):
    next_step: Literal["researcher", "coder", "FINISH"] = Field(
        description="The next specialized worker to invoke or FINISH if complete."
    )


supervisor_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def supervisor_node(state: TeamState) -> dict[str, str]:
    prompt = [
        SystemMessage(content="You are a supervisor managing 'researcher' and 'coder'. Choose who should act next."),
        *state["messages"],
    ]
    decision = supervisor_llm.with_structured_output(RouterDecision).invoke(prompt)
    return {"next_worker": decision.next_step}


def researcher_node(state: TeamState) -> dict[str, list[BaseMessage]]:
    return {"messages": [HumanMessage(content="[Researcher]: Gathered required background data.")]}


def coder_node(state: TeamState) -> dict[str, list[BaseMessage]]:
    return {"messages": [HumanMessage(content="[Coder]: Implemented clean Python script.")]}


def route_supervisor(state: TeamState) -> str:
    if state["next_worker"] == "FINISH":
        return END
    return state["next_worker"]


builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("coder", coder_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {"researcher": "researcher", "coder": "coder", END: END},
)
builder.add_edge("researcher", "supervisor")
builder.add_edge("coder", "supervisor")

team_graph = builder.compile()
```

---

## Example 4: Human-in-the-Loop Approval Workflow with Interrupt

```python
"""Interrupting execution for human approval before critical action execution."""

from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command


class DeploymentState(TypedDict):
    service_name: str
    environment: str
    approved: bool
    status: str


def prepare_deployment(state: DeploymentState) -> dict[str, str]:
    return {"status": f"Pending approval to deploy {state['service_name']} to {state['environment']}"}


def approval_gate(state: DeploymentState) -> dict[str, bool]:
    # Pauses graph execution until human sends input via Command(resume=...)
    human_response = interrupt({
        "question": f"Do you approve deployment of {state['service_name']} to {state['environment']}?",
        "options": ["yes", "no"],
    })
    is_approved = human_response.strip().lower() == "yes"
    return {"approved": is_approved}


def deploy_service(state: DeploymentState) -> dict[str, str]:
    if state["approved"]:
        return {"status": f"Successfully deployed {state['service_name']}!"}
    return {"status": f"Deployment of {state['service_name']} was aborted by user."}


builder = StateGraph(DeploymentState)
builder.add_node("prepare", prepare_deployment)
builder.add_node("approval", approval_gate)
builder.add_node("deploy", deploy_service)

builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approval")
builder.add_edge("approval", "deploy")
builder.add_edge("deploy", END)

checkpointer = MemorySaver()
deploy_graph = builder.compile(checkpointer=checkpointer)

# Execution flow:
# 1. run = deploy_graph.invoke({"service_name": "agent-api", "environment": "production"}, config={"configurable": {"thread_id": "dep-1"}})
# (Execution pauses at approval_gate)
# 2. resume = deploy_graph.invoke(Command(resume="yes"), config={"configurable": {"thread_id": "dep-1"}})
```
