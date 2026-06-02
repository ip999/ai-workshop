# AI Workshop — Training Materials

Instructor slides for delivering the [AI Workshop](../README.md) in a classroom. The slides front the concepts; delegates then build the examples themselves, working from the **🧪 Your turn** exercises embedded in each tutorial. There's no separate lab sheet — the tutorial *is* the lab.

So a lesson has just two layers:

- **Slides** (`training/slides/`) — what the instructor presents.
- **Tutorial** (in the repo) — what delegates read *and do*; each Part ends with a hands-on exercise.

One lesson maps to one tutorial:

| # | Lesson | Slides | Tutorial (read + do) |
|---|--------|--------|----------------------|
| 1 | From Completions to Agents | [slides/01-agents.md](slides/01-agents.md) | [agents/agents.md](../agents/agents.md) |
| 2 | From a Function to an MCP Server | [slides/02-mcp.md](slides/02-mcp.md) | [mcp/mcp.md](../mcp/mcp.md) |
| 3 | From a System Prompt to a Skill | [slides/03-skills.md](slides/03-skills.md) | [skills/skills.md](../skills/skills.md) |
| 4 | From a Message List to Memory | [slides/04-memory.md](slides/04-memory.md) | [memory/memory.md](../memory/memory.md) |
| 5 | Bringing It All Together | [slides/05-capstone.md](slides/05-capstone.md) | [capstone/capstone.md](../capstone/capstone.md) |

## The slides are [Marp](https://marp.app)

**Present from your browser, no setup:** the decks auto-render to GitHub Pages on every push to `main` via [`.github/workflows/slides.yml`](../.github/workflows/slides.yml). Once Pages is enabled (repo **Settings → Pages → Source: GitHub Actions**), present from:

> **https://ip999.github.io/ai-workshop/**

Open a deck, then use arrow keys to navigate, `F` for fullscreen, `P` for presenter view (speaker notes, timer, next-slide preview).

To build or edit locally instead, each deck is plain Markdown with `---` between slides:

- **VS Code:** install the **Marp for VS Code** extension, open a deck, and use the preview / "Export slide deck…".
- **CLI:** `npx @marp-team/marp-cli@latest slides/01-agents.md --html -o 01-agents.html` (or `--pdf`, `--pptx`).
- **Live, with a watch server:** `npx @marp-team/marp-cli@latest -s slides/` then open the printed URL.

Nothing about the content is Marp-specific — if you prefer Slidev, reveal-md, or Google Slides, the prose and code lift across with minor wrapper changes.

## Running a session

A lesson is designed for roughly **45–75 minutes**: ~20–30 min presenting the deck, the rest spent on the exercises. The deck's 🧪 **Your turn** slides mark where to pause and let delegates do the matching exercise in the tutorial.

**Before the room starts**, delegates need:

- **Python 3.10+** and an **OpenAI API key** in `OPENAI_API_KEY` ([get one](https://platform.openai.com/api-keys)).
- **Docker** for the sandbox exercises (Lesson 1 from the shell example onward, and the capstone).
- The fastest zero-setup path is the repo's **[Codespace](../README.md#run-it-in-the-browser-no-local-setup)** — Python and Docker preinstalled; delegates only add their key.

## How the two layers fit

- **Slides** — what the instructor talks to. Concepts and the key code, kept skimmable, with 🧪 Your turn slides marking the breaks.
- **Tutorial** — the full written walk-through delegates read, with a 🧪 Your turn exercise (do it → ✅ check → 🚀 stretch) at the end of each Part. It doubles as the self-service course and the lab.

Keeping the deck's checkpoints aligned with the tutorial's exercises is part of the process — see [guidelines.md](../guidelines.md#keeping-the-training-materials-in-sync).
