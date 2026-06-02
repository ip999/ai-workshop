# AI Workshop

A hands-on course on building LLM agents, plus a capstone that wires the ideas together. Each lesson teaches **one concept** through the smallest code that demonstrates it — no error handling, no abstractions, just the *shape* of the idea. It's linear: each lesson builds on the one before, so read them in order.

Fuzzy on *agent* vs *harness* vs *tool*? The [glossary](GLOSSARY.md) defines the terms this course uses — and is honest about where the field hasn't agreed.

## Run it in the browser (no local setup)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ip999/ai-workshop)

Click the badge to launch a [Codespace](https://github.com/features/codespaces) — a Linux dev environment in your browser with Python, Docker, and every dependency already installed (see [`.devcontainer`](.devcontainer/devcontainer.json)). It runs everything in this repo, including the Docker-based sandbox examples. You only need to provide an OpenAI key:

1. Add `OPENAI_API_KEY` as a [Codespaces secret](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces) (Settings → Codespaces → Secrets), or `export OPENAI_API_KEY=...` once the terminal opens.
2. Open any tutorial and run its code blocks in the terminal.

## Prerequisites

If you'd rather run locally instead of in Codespaces, you'll need:

- **Python 3.10+**
- **An OpenAI API key** in `OPENAI_API_KEY` — every tutorial except the MCP one calls the OpenAI API. Create one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). (This is the one thing Codespaces can't provide for you; the calls cost money against your own account.)
- **Docker** — needed for the sandboxed-shell examples ([agents.md](agents/agents.md) Part 6 onward) and the [capstone](capstone/capstone.md). The earlier tutorials run without it.

Each tutorial lists its own `pip install` line at the top, since the dependencies vary (the MCP course uses FastMCP and httpx; the rest just need `openai`).

## The tutorials

The lessons build the agent in layers — tools, then instructions, then state:

1. **[From Completions to Agents](agents/agents.md)** — start here. What an "agent" actually is: a model, some tools, and a loop. Ends with an agent driving a sandboxed shell.
2. **[From a Function to an MCP Server](mcp/mcp.md)** — where tools come from when you didn't write them: expose tools over the Model Context Protocol so any agent can use them.
3. **[From a System Prompt to a Skill](skills/skills.md)** — give the agent durable, reusable know-how it loads from disk on demand, instead of an ever-growing system prompt.
4. **[From a Message List to Memory](memory/memory.md)** — short-term memory (compaction) and long-term memory (a file the agent writes), so the agent stays coherent and remembers you across sessions.

Each lesson assumes the ones before it and ends pointing to the next.

## The capstone

**[Bringing It All Together](capstone/capstone.md)** — a single runnable agent ([agent.py](capstone/agent.py)) with an interactive loop (type a request, get an answer), a sandboxed shell, file tools, and memory that survives between runs. The smallest honest sketch of a general-purpose terminal agent, with each part traced back to the tutorial it came from.

## For contributors

**[guidelines.md](guidelines.md)** — the style and structure every tutorial follows. Read it before writing or editing a piece. The reference implementation is [agents/agents.md](agents/agents.md).
