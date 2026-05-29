# AI Workshop

A small collection of hands-on intros to building LLM agents, plus a capstone that wires the ideas together. Each tutorial teaches **one concept** through the smallest code that demonstrates it — no error handling, no abstractions, just the *shape* of the idea. They're written to be read in any order, but the order below builds most naturally.

## Run it in the browser (no local setup)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ip999/ai-workshop)

Click the badge to launch a [Codespace](https://github.com/features/codespaces) — a Linux dev environment in your browser with Python, Docker, and every dependency already installed (see [`.devcontainer`](.devcontainer/devcontainer.json)). It runs everything in this repo, including the Docker-based sandbox examples. You only need to provide an OpenAI key:

1. Add `OPENAI_API_KEY` as a [Codespaces secret](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces) (Settings → Codespaces → Secrets), or `export OPENAI_API_KEY=...` once the terminal opens.
2. Open any tutorial and run its code blocks in the terminal.

## Prerequisites

If you'd rather run locally instead of in Codespaces, you'll need:

- **Python 3.10+**
- **An OpenAI API key** in `OPENAI_API_KEY` — every tutorial except the MCP one calls the OpenAI API. (This is the one thing Codespaces can't provide for you; the calls cost money against your own account.)
- **Docker** — needed for the sandboxed-shell examples ([agents.md](agents/agents.md) Part 6 onward) and the [capstone](capstone/capstone.md). The earlier tutorials run without it.

Each tutorial lists its own `pip install` line at the top, since the dependencies vary (the MCP course uses FastMCP and httpx; the rest just need `openai`).

## The tutorials

1. **[From Completions to Agents](agents/agents.md)** — start here. What an "agent" actually is: a model, some tools, and a loop. Builds up to an agent with a sandboxed shell and a folder of skills.
2. **[From a System Prompt to a Skill](skills/skills.md)** — give an agent durable, reusable knowledge it loads from disk on demand, instead of one ever-growing system prompt.
3. **[From a Function to an MCP Server](mcp/mcp.md)** — expose your tools over the Model Context Protocol so any MCP-compatible agent can use them.
4. **[From a Message List to Memory](memory/memory.md)** — short-term memory (compaction) and long-term memory (a file the agent writes), so an agent stays coherent and remembers you across sessions.

Tutorials 2–4 each build on the agent loop from the first, but stand alone otherwise.

## The capstone

**[Bringing It All Together](capstone/capstone.md)** — a single runnable agent ([agent.py](capstone/agent.py)) with an interactive REPL (Read-Evaluate-Print-Loop), a sandboxed shell, file tools, and memory that survives between runs. The smallest honest sketch of a coding-style assistant, with each part traced back to the tutorial it came from.

## For contributors

**[guidelines.md](guidelines.md)** — the style and structure every tutorial follows. Read it before writing or editing a piece. The reference implementation is [agents/agents.md](agents/agents.md).
