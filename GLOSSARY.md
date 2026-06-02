# Glossary

The honest headline first: **neither "agent" nor "harness" has a single, universally accepted definition** — and that lack of consensus is itself the consensus finding. The most deliberate attempt to pin these down, [Hugging Face's agent glossary](https://github.com/huggingface/blog/blob/main/agent-glossary.md), opens by noting that many of these terms have no agreed meaning and different frameworks use the same word differently.

What *does* exist is a strong convergent core plus a few genuinely contested edges. These are the definitions **this course uses** — pragmatic, not authoritative. Read the sources at the bottom and make up your own mind.

## Agent

> **An LLM-driven system that pursues a goal by reasoning and acting in a loop, using tools and feedback from its environment, while directing its own steps rather than following a fixed script.**

The convergent core — the ingredients almost everyone agrees on:

1. an **LLM** as the decision-maker,
2. **tools** to act on an environment,
3. a **feedback loop** (act → observe → act again), and
4. **model-driven control** over the steps (autonomy).

How the leading voices put it:

- **Anthropic** ([Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)): agents are systems where *"LLMs dynamically direct their own processes and tool usage."* They contrast this with **workflows**, where models and tools run on predefined code paths. The crisp version (Barry Zhang): *with a workflow you own the control flow; with an agent, the model owns the plumbing.*
- **OpenAI** ([A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)): *"systems that independently accomplish tasks on your behalf"* — a model (reasoning) + tools (acting) + instructions/guardrails, looping until an exit condition is met.
- **The root** is reinforcement learning: an agent takes an *observation* and returns an *action*; the environment returns a new observation; repeat. That loop is still the heart of an LLM agent.

**Where it's contested — the degree of autonomy.** Anthropic reads "agent" narrowly (true model-directed control) and files predefined pipelines under "workflow," with both under the umbrella *agentic systems*. Other frameworks call prescriptive, task-assigned pipelines "agents" too. So **"agentic" is best read as a spectrum**, and a given product can sit anywhere on it.

## Harness

> **The software layer around the model that runs that loop — invoking the model, executing its tool calls, managing context, memory, and state, enforcing guardrails, and deciding when to stop.**

The term is borrowed from software testing ("test harness"). Two converging usages:

- **Production usage.** Anthropic's own copy is a clean primary source: Claude Code is the *agentic harness around Claude* — the tools, context management, and execution environment that turn a language model into a capable agent. The community shorthand, from Mitchell Hashimoto and popularized by [Addy Osmani](https://addyosmani.com/blog/agent-harness-engineering/), is the formula **Agent = Model + Harness** — *"if you're not the model, you're the harness."* Osmani's punchline: on SWE-bench, swapping the *harness* moved scores ~22 points while swapping the *model* moved them ~1 — the model is a commodity; the harness is the moat.
- **Evaluation usage.** In safety/eval work, the harness is the interface used to elicit a model's capabilities — and its choices (context management, tool access, retries, scoring, budgets) materially change the result. Research often calls this same thing the **scaffold** / scaffolding.

**The nuance most people skip** (since you're here for precision): some careful sources separate the two —

- **Scaffold** = the *behavior-defining* layer: the system prompt, tool descriptions, how responses are parsed, what the model remembers across steps.
- **Harness** = the *execution* layer that makes the agent run: it calls the model, handles its tool calls, and decides when to stop.

But in broad/common usage — including Anthropic's — **"harness" means everything that isn't the model**, absorbing the scaffold into it. The fine distinction mostly matters when you reason about the two separately (e.g. in a training or eval pipeline).

## Putting them together

**The agent is the whole system; the model is its reasoning core; the harness is everything wrapped around the model that lets it act in a loop.**

Empirically, the harness is *most* of the engineering. A reverse-engineering study of Claude Code's leaked bundle ([Dive into Claude Code](https://github.com/VILA-Lab/Dive-into-Claude-Code)) estimated roughly **1.6% of the codebase is AI decision logic and ~98.4% is operational infrastructure** — permissions, context management, safety, tools, session persistence. Treat the exact ratio cautiously (it's line-counting on a leak-derived bundle), but the qualitative point holds: *the core agent loop is a trivially simple while-loop, and almost everything that makes a production agent reliable lives in the harness around it.*

That is exactly what this course shows in miniature: the [capstone](capstone/capstone.md)'s loop is ~12 lines, and the rest of `agent.py` is harness. A *minimal* harness is small on purpose; a *production* one balloons.

## Other terms, briefly

- **Model / LLM** — the stateless reasoning core. Reads the messages, returns the next step (a tool request or a final answer). Can't loop or act on its own.
- **Tool** — a function the model can *request*; the harness executes it and feeds the result back.
- **Loop (agent loop)** — call the model → run any tool calls → feed back the results → repeat until it stops asking for tools. ([agents.md](agents/agents.md) Part 4.)
- **Workflow** — (Anthropic's contrast) an LLM + tools on a *predefined* code path; *you* own the control flow. Not an agent, but agent-adjacent.
- **Skill** — durable, file-based know-how the agent loads on demand. ([skills.md](skills/skills.md).)
- **Memory** — short-term (the message list / compaction) and long-term (a file the agent writes). ([memory.md](memory/memory.md).)
- **MCP (Model Context Protocol)** — a standard for exposing tools to any agent, regardless of who wrote them. ([mcp.md](mcp/mcp.md).)
- **Sandbox** — an isolated environment (we use Docker) so the agent's commands can't touch your real machine. A *choice* driven by tool power, not a fixed requirement.

## Sources (read widely — there's no settled answer)

- [Hugging Face — agent glossary](https://github.com/huggingface/blog/blob/main/agent-glossary.md) — the deliberate "no universal definitions" take; formalizes model + harness and the scaffold/harness split.
- [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — agents vs workflows.
- [OpenAI — A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) — model + tools + instructions, looping to an exit condition.
- [Addy Osmani — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/) — "Agent = Model + Harness."
- [Dive into Claude Code (VILA-Lab)](https://github.com/VILA-Lab/Dive-into-Claude-Code) — the ~1.6% / ~98.4% analysis.
- [Lilian Weng — LLM-Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) — the older "agent = LLM + planning + memory + tools" view, for contrast.
