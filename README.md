# AI Workshop

A small collection of hands-on intros to building LLM agents, plus a capstone that wires the ideas together. Each tutorial teaches **one concept** through the smallest code that demonstrates it — no error handling, no abstractions, just the *shape* of the idea. They're written to be read in any order, but the order below builds most naturally.

## The tutorials

1. **[From Completions to Agents](agents/agents.md)** — start here. What an "agent" actually is: a model, some tools, and a loop. Builds up to an agent with a sandboxed shell and a folder of skills.
2. **[From a System Prompt to a Skill](skills/skills.md)** — give an agent durable, reusable knowledge it loads from disk on demand, instead of one ever-growing system prompt.
3. **[From a Function to an MCP Server](mcp/mcp.md)** — expose your tools over the Model Context Protocol so any MCP-compatible agent can use them.
4. **[From a Message List to Memory](memory/memory.md)** — short-term memory (compaction) and long-term memory (a file the agent writes), so an agent stays coherent and remembers you across sessions.

Tutorials 2–4 each build on the agent loop from the first, but stand alone otherwise.

## The capstone

**[Bringing It All Together](capstone/capstone.md)** — a single runnable agent ([agent.py](capstone/agent.py)) with an interactive REPL, a sandboxed shell, file tools, and memory that survives between runs. The smallest honest sketch of a coding-style assistant, with each part traced back to the tutorial it came from.

## For contributors

**[guidelines.md](guidelines.md)** — the style and structure every tutorial follows. Read it before writing or editing a piece. The reference implementation is [agents/agents.md](agents/agents.md).
