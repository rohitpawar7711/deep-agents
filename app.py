"""
Deep Agents Conversational Chatbot (Streamlit)
================================================
A single chat UI that exercises every feature covered in the project's
notebooks:

  1-basic.ipynb              -> create_deep_agent(model, tools, system_prompt)
  2-backends.ipynb           -> StateBackend / FilesystemBackend / StoreBackend
  3-context-enginneering.ipynb -> checkpointer (threads), memory=["/Agents.md"],
                                   skills=["/skills"]
  4-subagents.ipynb          -> subagents=[...] delegated via the "task" tool,
                                   with an optional structured response_format

Everything is configurable from the sidebar; the agent is rebuilt whenever
the configuration changes and cached in st.session_state otherwise.
"""

import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

for key in ("OPENAI_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY"):
    if os.getenv(key):
        os.environ[key] = os.getenv(key)

from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents import create_deep_agent
from deepagents.backends import StateBackend, FilesystemBackend, StoreBackend
from deepagents.backends.utils import create_file_data

ROOT_DIR = Path(__file__).parent
AGENTS_MD_PATH = ROOT_DIR / "projects" / "Agents.md"
SKILLS_DIR = ROOT_DIR / "skills"
SKILL_NAMES = ["langgraph", "python", "docker", "report-writing"]

st.set_page_config(page_title="Deep Agents Chatbot", page_icon="🤖", layout="wide")


# ---------------------------------------------------------------------------
# Tools (1-basic.ipynb / 4-subagents.ipynb)
# ---------------------------------------------------------------------------
def _make_web_search_tool():
    """Tavily-backed web_search tool, identical to the one in 1-basic.ipynb."""
    from typing import Literal
    from tavily import TavilyClient
    from langchain.tools import tool

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    @tool
    def web_search(
        query: str,
        topic: Literal["sports", "news", "finance", "general"] = "general",
        max_results: int = 5,
        include_raw_content: bool = False,
    ):
        """Run a web search."""
        return client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )

    return web_search


class ResearchFindings(BaseModel):
    """Structured findings from a research subagent (4-subagents.ipynb)."""

    summary: str = Field(description="Summary of findings")
    confidence: float = Field(description="Confidence score from 0 to 1")
    sources: list[str] = Field(description="List of source URLs")


def _make_research_subagent(model: str, structured: bool):
    web_search = _make_web_search_tool()
    subagent = {
        "name": "research-subagent",
        "description": (
            "Use this subagent proactively for requests requiring in-depth "
            "internet research, fact-finding, or a detailed technical report. "
            "It searches the web and returns a structured summary with sources."
        ),
        "system_prompt": (
            "You are a research specialist. Use the web_search tool to "
            "investigate the assigned topic. Gather relevant evidence, compare "
            "findings where useful, and return a detailed, well-structured "
            "report with source URLs."
        ),
        "tools": [web_search],
        "model": model,
    }
    if structured:
        subagent["response_format"] = ResearchFindings
    return subagent


# ---------------------------------------------------------------------------
# Memory / Skills file loading (3-context-enginneering.ipynb)
# ---------------------------------------------------------------------------
def _load_agents_md_files():
    if not AGENTS_MD_PATH.exists():
        return {}
    content = AGENTS_MD_PATH.read_text(encoding="utf-8")
    return {"/projects/Agents.md": create_file_data(content)}


def _load_skill_files():
    files = {}
    for name in SKILL_NAMES:
        skill_path = SKILLS_DIR / name / "SKILL.md"
        if skill_path.exists():
            files[f"/skills/{name}/SKILL.md"] = create_file_data(
                skill_path.read_text(encoding="utf-8")
            )
    return files


# ---------------------------------------------------------------------------
# Agent construction
# ---------------------------------------------------------------------------
def build_agent(config: dict):
    """Build a deep agent according to the sidebar configuration."""
    model = config["model"]
    backend_choice = config["backend"]
    use_memory = config["use_memory"]
    use_skills = config["use_skills"]
    use_subagent = config["use_subagent"]
    structured_subagent = config["structured_subagent"]
    store = config["store"]
    namespace_key = config["namespace_key"]

    tools = []
    if config["use_web_search"] and os.getenv("TAVILY_API_KEY"):
        tools.append(_make_web_search_tool())

    subagents = []
    if use_subagent and os.getenv("TAVILY_API_KEY"):
        subagents.append(_make_research_subagent(model, structured_subagent))

    # --- Backend (2-backends.ipynb) ---
    if backend_choice == "StateBackend (in-memory, ephemeral)":
        backend = StateBackend()
    elif backend_choice == "FilesystemBackend (writes to disk, sandboxed)":
        backend = FilesystemBackend(root_dir=str(ROOT_DIR), virtual_mode=True)
    else:  # StoreBackend (cross-thread persistence)
        backend = StoreBackend(
            store=store,
            namespace=lambda rt: (namespace_key,),
        )

    kwargs = dict(
        model=model,
        tools=tools,
        system_prompt=config["system_prompt"],
        backend=backend,
        checkpointer=MemorySaver(),
    )
    if subagents:
        kwargs["subagents"] = subagents
    if use_memory:
        kwargs["memory"] = ["/projects/Agents.md"]
    if use_skills:
        kwargs["skills"] = ["/skills"]
    if backend_choice.startswith("StoreBackend"):
        kwargs["store"] = store

    return create_deep_agent(**kwargs)


def build_invoke_files(config: dict):
    """Seed state['files'] for backends that don't read straight from disk."""
    files = {}
    if config["backend"].startswith("StateBackend") or config["backend"].startswith(
        "StoreBackend"
    ):
        if config["use_memory"]:
            files.update(_load_agents_md_files())
        if config["use_skills"]:
            files.update(_load_skill_files())
    return files


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("🤖 Deep Agents — Config")

model = st.sidebar.selectbox(
    "Model",
    [
        "openai:gpt-5.5",
        "openai:gpt-5.4",
        "openai:gpt-5.4-nano-2026-03-17",
        "groq:openai/gpt-oss-120b",
    ],
    index=0,
)

backend_choice = st.sidebar.radio(
    "Backend (2-backends.ipynb)",
    [
        "StateBackend (in-memory, ephemeral)",
        "FilesystemBackend (writes to disk, sandboxed)",
        "StoreBackend (cross-thread persistence)",
    ],
    help=(
        "StateBackend: files live only in graph state for this run.\n"
        "FilesystemBackend: files are really written under this project's "
        "directory (virtual_mode sandboxes paths to it).\n"
        "StoreBackend: files persist across chat threads via a LangGraph "
        "store, keyed by a namespace."
    ),
)

namespace_key = st.sidebar.text_input(
    "StoreBackend namespace",
    value="rohitp-demo-user",
    help="Only used for StoreBackend — files/memory persist across threads under this key.",
    disabled=not backend_choice.startswith("StoreBackend"),
)

st.sidebar.divider()
st.sidebar.subheader("Context engineering (3-context-enginneering.ipynb)")
use_memory = st.sidebar.checkbox(
    "Load projects/Agents.md as durable memory", value=True
)
use_skills = st.sidebar.checkbox(
    "Enable skills (langgraph, python, docker, report-writing)", value=True
)

st.sidebar.divider()
st.sidebar.subheader("Tools & Subagents (1-basic / 4-subagents)")
use_web_search = st.sidebar.checkbox(
    "Give the main agent a web_search tool (Tavily)",
    value=bool(os.getenv("TAVILY_API_KEY")),
    disabled=not os.getenv("TAVILY_API_KEY"),
)
use_subagent = st.sidebar.checkbox(
    "Enable research-subagent (delegated via the task tool)",
    value=bool(os.getenv("TAVILY_API_KEY")),
    disabled=not os.getenv("TAVILY_API_KEY"),
)
structured_subagent = st.sidebar.checkbox(
    "Subagent returns structured output (Pydantic response_format)",
    value=False,
    disabled=not use_subagent,
)

if not os.getenv("TAVILY_API_KEY"):
    st.sidebar.warning("TAVILY_API_KEY not set — web search & subagent disabled.")

st.sidebar.divider()
system_prompt = st.sidebar.text_area(
    "System prompt",
    value=(
        "You are the main assistant for a deep-agents demo. For requests "
        "requiring in-depth internet research, delegate to the "
        "research-subagent using the task tool, then summarize its findings. "
        "Use your filesystem tools (read_file/write_file/edit_file/"
        "list_directory) whenever the user asks you to create, read, or "
        "update files. Do not claim to have delegated or written a file "
        "unless you actually called the tool."
    ),
    height=130,
)

config = {
    "model": model,
    "backend": backend_choice,
    "namespace_key": namespace_key,
    "use_memory": use_memory,
    "use_skills": use_skills,
    "use_web_search": use_web_search,
    "use_subagent": use_subagent,
    "structured_subagent": structured_subagent,
    "system_prompt": system_prompt,
}

# Persist a single InMemoryStore across reruns so StoreBackend data survives
# "New conversation" (new thread_id) the way 2-backends.ipynb demonstrates.
if "store" not in st.session_state:
    st.session_state.store = InMemoryStore()
config["store"] = st.session_state.store

config_fingerprint = (
    model,
    backend_choice,
    namespace_key,
    use_memory,
    use_skills,
    use_web_search,
    use_subagent,
    structured_subagent,
    system_prompt,
)

rebuild = (
    "agent" not in st.session_state
    or st.session_state.get("config_fingerprint") != config_fingerprint
)

st.sidebar.divider()
if st.sidebar.button("🔁 New conversation (new thread_id)"):
    st.session_state.thread_id = str(uuid4())
    st.session_state.chat_history = []
    rebuild = True

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if rebuild:
    try:
        st.session_state.agent = build_agent(config)
        st.session_state.config_fingerprint = config_fingerprint
        st.session_state.build_error = None
    except Exception as exc:  # surfaced in the main pane
        st.session_state.agent = None
        st.session_state.build_error = str(exc)

st.sidebar.caption(f"Thread ID: `{st.session_state.thread_id}`")

# ---------------------------------------------------------------------------
# Main pane
# ---------------------------------------------------------------------------
st.title("Deep Agents Conversational Chatbot")
st.caption(
    "Exercises create_deep_agent's backends, memory, skills, checkpointing "
    "and subagent delegation, all from one chat."
)

if st.session_state.get("build_error"):
    st.error(f"Failed to build agent: {st.session_state.build_error}")
    st.stop()

tab_chat, tab_files, tab_about = st.tabs(["💬 Chat", "🗂️ Virtual Filesystem", "ℹ️ Features"])

with tab_chat:
    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("trace"):
                with st.expander("Agent trace (tool calls / subagent delegation)"):
                    st.code(turn["trace"], language="text")

    user_input = st.chat_input("Ask the deep agent anything...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        invoke_payload = {"messages": [{"role": "user", "content": user_input}]}
        seed_files = build_invoke_files(config)
        if seed_files:
            invoke_payload["files"] = seed_files

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.agent.invoke(
                        invoke_payload,
                        config={"configurable": {"thread_id": st.session_state.thread_id}},
                    )
                    reply = result["messages"][-1].content
                    if isinstance(reply, list):
                        reply = "\n".join(
                            part.get("text", "") if isinstance(part, dict) else str(part)
                            for part in reply
                        )

                    trace_lines = []
                    for m in result["messages"]:
                        tool_calls = getattr(m, "tool_calls", None)
                        if tool_calls:
                            for tc in tool_calls:
                                trace_lines.append(f"-> called tool: {tc['name']}({tc.get('args')})")
                        elif type(m).__name__ == "ToolMessage":
                            trace_lines.append(
                                f"<- tool result [{getattr(m, 'name', '?')}]: "
                                f"{str(m.content)[:300]}"
                            )
                    trace = "\n".join(trace_lines) if trace_lines else None

                    st.markdown(reply)
                    if trace:
                        with st.expander("Agent trace (tool calls / subagent delegation)"):
                            st.code(trace, language="text")

                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": reply, "trace": trace}
                    )
                    st.session_state.last_result = result
                except Exception as exc:
                    st.error(f"Agent invocation failed: {exc}")

with tab_files:
    st.subheader("Virtual filesystem")
    last_result = st.session_state.get("last_result")
    if backend_choice.startswith("FilesystemBackend"):
        st.caption(f"FilesystemBackend writes under: `{ROOT_DIR}`")
        found_any = False
        for p in ROOT_DIR.rglob("*"):
            if p.is_file() and ".venv" not in p.parts and p.suffix in (".txt", ".md", ".json"):
                rel = p.relative_to(ROOT_DIR)
                if str(rel).startswith("notes") or str(rel).startswith("projects"):
                    found_any = True
                    with st.expander(str(rel)):
                        st.code(p.read_text(encoding="utf-8"))
        if not found_any:
            st.info("No files written to disk yet. Ask the agent to create one.")
    elif last_result and last_result.get("files"):
        for path, data in last_result["files"].items():
            with st.expander(path):
                content = data.get("content") if isinstance(data, dict) else data
                st.code(content)
    else:
        st.info(
            "No files in agent state yet for this backend. Ask the agent to "
            "create a file, e.g. \"Create /notes/todo.txt with ...\"."
        )

with tab_about:
    st.markdown(
        """
### Notebook features wired into this app

| Notebook | Feature | Where in this app |
|---|---|---|
| `1-basic.ipynb` | `create_deep_agent(model, tools, system_prompt)` | Sidebar model + web_search tool |
| `1-basic.ipynb` | Tavily `web_search` tool | "Give the main agent a web_search tool" |
| `2-backends.ipynb` | `StateBackend` | Backend radio, option 1 |
| `2-backends.ipynb` | `FilesystemBackend(root_dir, virtual_mode=True)` | Backend radio, option 2 (see 🗂️ tab) |
| `2-backends.ipynb` | `StoreBackend` + `InMemoryStore` + namespace | Backend radio, option 3 |
| `2-backends.ipynb` | Cross-thread persistence via thread IDs | "New conversation" button + thread id |
| `3-context-enginneering.ipynb` | `checkpointer=MemorySaver()` | Always on, keyed by thread_id |
| `3-context-enginneering.ipynb` | `memory=["/projects/Agents.md"]` | "Load Agents.md as durable memory" |
| `3-context-enginneering.ipynb` | `skills=["/skills"]` + progressive disclosure | "Enable skills" checkbox |
| `4-subagents.ipynb` | Synchronous `subagents=[...]`, delegated via `task` tool | "Enable research-subagent" |
| `4-subagents.ipynb` | Subagent structured output (`response_format`) | "Subagent returns structured output" |

Toggle any combination in the sidebar — the agent is rebuilt automatically.
The **Agent trace** expander under each reply shows tool calls (including
delegation to the subagent via the `task` tool) so you can see the deep
agent's internals at work.
        """
    )
