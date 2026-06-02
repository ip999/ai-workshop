# AI Workshop — Training Materials

Instructor slides and hands-on labs for delivering the [AI Workshop](../README.md) in a classroom. The slides front the concepts; the delegates then build the examples themselves as labs, using the tutorials in the repo as the full reference.

One lesson maps to one tutorial:

| # | Lesson | Slides | Lab | Reference |
|---|--------|--------|-----|-----------|
| 1 | From Completions to Agents | [slides/01-agents.md](slides/01-agents.md) | [labs/01-agents.md](labs/01-agents.md) | [agents/agents.md](../agents/agents.md) |
| 2 | From a Function to an MCP Server | _(planned)_ | _(planned)_ | [mcp/mcp.md](../mcp/mcp.md) |
| 3 | From a System Prompt to a Skill | _(planned)_ | _(planned)_ | [skills/skills.md](../skills/skills.md) |
| 4 | From a Message List to Memory | _(planned)_ | _(planned)_ | [memory/memory.md](../memory/memory.md) |
| 5 | Bringing It All Together | _(planned)_ | _(planned)_ | [capstone/capstone.md](../capstone/capstone.md) |

## The slides are [Marp](https://marp.app)

Each deck is plain Markdown with `---` between slides. To present or export:

- **VS Code:** install the **Marp for VS Code** extension, open a deck, and use the preview / "Export slide deck…".
- **CLI:** `npx @marp-team/marp-cli@latest slides/01-agents.md --html -o 01-agents.html` (or `--pdf`, `--pptx`).
- **Live, with a watch server:** `npx @marp-team/marp-cli@latest -s slides/` then open the printed URL.

Nothing about the content is Marp-specific — if you prefer Slidev, reveal-md, or Google Slides, the prose and code lift across with minor wrapper changes.

## Running a session

A lesson is designed for roughly **45–75 minutes**: ~20–30 min presenting the deck, the rest spent on the lab. The deck has 🧪 **Lab checkpoint** slides that mark where to pause and let delegates work.

**Before the room starts**, delegates need:

- **Python 3.10+** and an **OpenAI API key** in `OPENAI_API_KEY` ([get one](https://platform.openai.com/api-keys)).
- **Docker** for the sandbox labs (Lesson 1 from the shell example onward, and the capstone).
- The fastest zero-setup path is the repo's **[Codespace](../README.md#run-it-in-the-browser-no-local-setup)** — Python and Docker preinstalled; delegates only add their key.

## How the three pieces fit

- **Slides** — what the instructor talks to. Concepts and the key code, kept skimmable.
- **Labs** — what delegates *do*. Step-by-step, with checkpoints and stretch goals.
- **Tutorials** (in the repo) — the full written walk-through delegates read alongside the lab.
