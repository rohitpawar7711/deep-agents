# DeepAgents Skills Library

This directory contains specialized domain skills for **DeepAgents**. Skills provide deep architectural guidelines, instructions, and concrete reference examples that agents consult dynamically via **progressive disclosure** when answering queries or executing tasks.

---

## Skills Directory Structure

```
skills/
├── python/                  # Python engineering, idioms, testing & optimization
│   ├── SKILL.md             # Frontmatter metadata & skill overview
│   ├── instruction.md       # Detailed coding & architectural rules
│   └── examples.md          # Production code examples & patterns
├── langgraph/               # LangGraph stateful multi-agent orchestration
│   ├── SKILL.md             # Frontmatter metadata & skill overview
│   ├── instruction.md       # State design, nodes, edges & checkpointers
│   └── examples.md          # ReAct, Multi-Agent & Human-in-the-Loop examples
├── docker/                  # Docker containerization, compose & security
│   ├── SKILL.md             # Frontmatter metadata & skill overview
│   ├── instruction.md       # Dockerfile optimization, multi-stage & security
│   └── examples.md          # Multi-stage Dockerfile, compose & .dockerignore
└── report-writing/          # Structured report writing & synthesis
    ├── SKILL.md             # Frontmatter metadata & skill overview
    ├── instruction.md       # Report blueprints, formatting & quality standards
    └── examples.md          # Architecture, RCA, and Benchmark report templates
```

---

## How DeepAgents Uses Skills

DeepAgents implements Anthropic's **Agent Skills** specification with **progressive disclosure**:

1. **Discovery & Injection**:
   When an agent is created with `skills=["skills"]` or using `SkillsMiddleware(backend=backend, sources=["skills"])`, the metadata from each skill's `SKILL.md` frontmatter is injected into the agent's system prompt:
   ```python
   from deepagents import create_deep_agent
   from deepagents.backends import FilesystemBackend

   backend = FilesystemBackend(root_dir=".", virtual_mode=True)

   agent = create_deep_agent(
       model="openai:gpt-5.4",
       backend=backend,
       skills=["skills"],
       memory=["/projects/Agents.md"],
   )
   ```

2. **Triggering via User Queries**:
   When the user asks a question related to Python, LangGraph, Docker, or requesting a report:
   - The agent checks its system prompt and identifies the matching skill.
   - The agent reads the skill's instructions using its built-in filesystem tools (`read_file(file_path="skills/<skill>/SKILL.md", limit=1000)`).
   - If deeper guidance is required, the agent reads `instruction.md` and `examples.md` to ground its reasoning, code generation, or report output.

3. **Standard Skill File Roles**:
   - `SKILL.md`: Mandatory YAML frontmatter (`name`, `description`, `compatibility`, `license`, `allowed-tools`) + executive overview.
   - `instruction.md`: Procedural rules, architecture principles, security guidelines, and edge-case handling.
   - `examples.md`: Complete, battle-tested code patterns and templates that can be directly adapted.
