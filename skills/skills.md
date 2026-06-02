# From a System Prompt to a Skill: A Hands-On Intro

A short follow-on for developers who've built [an agent](../agents/agents.md) and want to give it durable, reusable knowledge — how to do specific tasks, conventions to follow, things that would otherwise live in a forgotten Notion page. By the end you'll have a folder of skills that an agent picks up from disk and uses on demand.

We'll use OpenAI's API throughout. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of each idea clearly.

**Prerequisites:** Python 3.10+, an OpenAI API key in `OPENAI_API_KEY`, and `pip install openai`. Familiarity with the [agent loop](../agents/agents.md) helps but isn't required.

## Contents

1. [A System Prompt](#part-1-a-system-prompt)
2. [A Long System Prompt](#part-2-a-long-system-prompt)
3. [A Skill on Disk](#part-3-a-skill-on-disk)
4. [The Skill Index](#part-4-the-skill-index)
5. [Skills That Ship Code](#part-5-skills-that-ship-code)
6. [Writing a Description That Triggers](#part-6-writing-a-description-that-triggers)
7. [Recap](#recap)
8. [Skills or a tool?](#skills-or-a-tool)
9. [But what about RAG?](#but-what-about-rag)
10. [Further reading](#further-reading)

---

## Part 1: A System Prompt

The simplest way to give an agent instructions is to put them in the system prompt.

```python
# describe_csv.py
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "When summarizing CSVs, always report row count, column names, and one example row."},
        {"role": "user", "content": "Summarize this CSV:\nname,age\nAda,36\nGrace,45"},
    ],
)
print(response.choices[0].message.content)
# Rows: 2. Columns: name, age. Example row: Ada, 36.
```

A few things to internalise:

- The system prompt is the agent's **standing instructions** — it sees them on every turn.
- This works fine for a sentence or two of guidance.
- Every token in the system prompt is paid for on every API call, and competes for the model's attention with everything else in context.

> **🧪 Your turn** — save the snippet above as `describe_csv.py` and run it.
>
> - ✅ The reply follows the system prompt's format (row count, columns, example row).
> - 🚀 Change the system prompt and watch the output shape change with it.

## Part 2: A Long System Prompt

What happens when you want the agent to know how to handle CSVs, *and* PDFs, *and* git operations, *and* your team's deployment conventions, *and* how to fill out expense reports?

```python
system_prompt = """
When summarizing CSVs, always report row count, column names, and one example row.
Detect the delimiter — it isn't always a comma.

When extracting text from PDFs, prefer pdfplumber over PyPDF2. If the PDF is
scanned, fall back to tesseract via pytesseract.

For git commits, our convention is conventional-commits. Squash before merging.
The main branch is protected; open a PR.

When deploying, always run the test suite first. Production deploys must go
through staging. The deploy script is at scripts/deploy.sh.

For expense reports, the categories are: travel, meals, software, hardware.
Receipts must be attached as PDFs, not images...
"""
```

Pretty soon you have a problem:

- The prompt bloats. Every call pays for instructions about PDFs even when the user asked about CSVs.
- The model has to mentally filter the relevant guidance out of a wall of unrelated text. Accuracy drops.
- Adding a new domain means editing this monolith and re-shipping. There's no version control of *the instructions themselves*, separate from the agent code.

There's a better way.

## Part 3: A Skill on Disk

Instead of stuffing instructions into the system prompt, put them in files. Give the agent a tool to read those files when relevant.

First, create a skill:

```
mkdir -p skills/csv
```

```markdown
# skills/csv/SKILL.md

When summarizing a CSV:

1. Detect the delimiter — try comma, semicolon, tab in that order.
2. Report row count, column names, and one example row.
3. If a column looks numeric, include min/max/mean.
```

Now the agent. We give it two tools: `read_file` for loading skills, and `bash` for actually doing work.

```python
from openai import OpenAI
import json
import subprocess

client = OpenAI()

def read_file(path):
    return open(path).read()

def bash(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from disk.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

system_prompt = (
    "You are an agent. Before doing a task, check if "
    "skills/csv/SKILL.md is relevant and read it if so."
)

# ... standard agent loop here — see ../agents/agents.md Part 4 ...
```

This works, but it doesn't scale either. You'd have to teach the agent about every skill by name in the system prompt — exactly the problem we just had. We need a way for the agent to *discover* skills.

## Part 4: The Skill Index

The trick: keep a short index of *all* skills in the system prompt — just their names and descriptions — and let the agent decide which one to read in full.

Each skill file gets a frontmatter block declaring its name and description:

```markdown
---
name: csv
description: Use when the user wants to summarize, filter, or analyze a CSV file.
---

# CSV skill

When summarizing a CSV:

1. Detect the delimiter — try comma, semicolon, tab in that order.
2. Report row count, column names, and one example row.
3. If a column looks numeric, include min/max/mean.
```

Now the agent builds an index from the frontmatter at startup and injects it into the system prompt:

```python
from pathlib import Path
import re

def build_skill_index(skills_dir="skills"):
    lines = []
    for skill_md in Path(skills_dir).glob("*/SKILL.md"):
        text = skill_md.read_text()
        name = re.search(r"^name:\s*(.+)$", text, re.M).group(1).strip()
        desc = re.search(r"^description:\s*(.+)$", text, re.M).group(1).strip()
        lines.append(f"- **{name}** (`{skill_md}`): {desc}")
    return "\n".join(lines)

system_prompt = f"""You are an agent. You have access to skills — prewritten instructions for common tasks. Before starting a task, check this index and read the relevant SKILL.md if one looks useful:

{build_skill_index()}

Use read_file to load a skill, then follow its instructions."""
```

The system prompt now contains *every skill's description*, but only the **descriptions** — typically a single sentence each. The agent calls `read_file("skills/csv/SKILL.md")` when (and only when) it actually needs the full instructions.

**This is the conceptual leap.** Context stays small even with hundreds of skills available, because the model uses its own judgment to decide what to load. You haven't taught the agent about CSVs in the prompt — you've taught it that a skill called "csv" exists, and let it decide whether to look at it.

You can add a new skill tomorrow by dropping a folder in `skills/`. No code change. No redeploy. The agent picks it up on its next run.

## Part 5: Skills That Ship Code

Instructions are useful, but skills get genuinely powerful when they bundle *code* alongside the instructions. A skill is a **folder**, not a file — the SKILL.md is just the entry point.

```
skills/csv/
├── SKILL.md
└── summarize.py
```

```python
# skills/csv/summarize.py
import csv, sys, statistics

path = sys.argv[1]
with open(path) as f:
    sample = f.read(2048)
    delimiter = csv.Sniffer().sniff(sample).delimiter
    f.seek(0)
    rows = list(csv.DictReader(f, delimiter=delimiter))

print(f"Rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys())}")
print(f"Example: {rows[0]}")

for col in rows[0]:
    values = [r[col] for r in rows]
    try:
        nums = [float(v) for v in values]
        print(f"{col}: min={min(nums)} max={max(nums)} mean={statistics.mean(nums):.2f}")
    except ValueError:
        pass
```

```markdown
---
name: csv
description: Use when the user wants to summarize, filter, or analyze a CSV file.
---

# CSV skill

To summarize a CSV file, run:

    python skills/csv/summarize.py <path-to-csv>

It prints row count, columns, one example row, and stats for numeric columns. It auto-detects the delimiter.

For more complex filtering or transformation, write your own Python using the `csv` module — the file may use any delimiter (comma, semicolon, tab).
```

Now when the agent reads SKILL.md, it learns that `summarize.py` exists and how to invoke it. It uses `bash` to run the script. The skill author has done the hard part — figured out delimiter sniffing, picked the right library — once, and every future agent invocation benefits.

This is the unlock. A skill is *frozen expertise* — the trial-and-error you'd otherwise repeat every conversation, packaged so the agent gets it right the first time.

> **🧪 Your turn** — create `skills/csv/` with `SKILL.md` and `summarize.py`, then run `python skills/csv/summarize.py <a-csv>`.
>
> - ✅ It prints row count, columns, an example row, and stats for numeric columns.
> - 🚀 Wire it into the indexed agent (Part 4) and ask it to summarize a CSV — watch it `cat` the SKILL.md, then run the script.

## Part 6: Writing a Description That Triggers

The single most important line in a skill is its description. It's the only part the agent sees by default, and it's what determines whether the skill gets used at all.

Compare these two:

```yaml
# Bad
description: CSV utilities.
```

```yaml
# Good
description: Use when the user wants to summarize, filter, analyze, or extract statistics from a CSV, TSV, or other delimited file. Covers delimiter detection and numeric-column stats.
```

The bad version is what the *author* thinks the skill is. The good version is written from the model's perspective — it lists the **trigger phrases** ("summarize", "filter", "analyze", "extract statistics"), the **adjacent file types** ("TSV", "delimited"), and what's actually inside ("delimiter detection", "numeric-column stats").

A few rules that come up over and over:

- **Lead with "Use when..."** — orients the model toward the triggering question rather than describing the artifact.
- **Include synonyms.** A user might say "summarize", "describe", "analyze", "look at". Cover the ones a reasonable user might say.
- **Mention edge cases the skill handles.** "Covers delimiter detection" tells the model this skill is the right choice even for unusual CSVs.
- **Don't oversell.** If the skill only summarizes, don't claim it filters. The model will pick it for a filtering task and then fail.

The same care applies to the SKILL.md body, but with a different priority: the body is read only when the description has already done its job. Optimize the description for *retrieval*, the body for *instruction-following*.

## Recap

You've now built three things:

1. **A system prompt** — instructions in context. Fine for a sentence; breaks down at scale.
2. **A skill on disk** — instructions in a file the agent reads on demand. Better, but the agent needs to know it exists.
3. **An indexed skills folder** — names and descriptions in context, full content loaded by judgment. Scales to hundreds of capabilities without bloating any individual conversation.

That's enough to give an agent durable, evolvable expertise. The next steps, once you want to go further:

- **Sandboxing.** Running `bash` and arbitrary skill scripts on your host is fine for learning. Production agents run skills inside Docker or a microVM. See [the agents course](../agents/agents.md) for one approach.
- **Skill versioning.** Keep skills in git. They're as much "source code" as your agent loop is, and benefit from review, history, and rollback.
- **Hierarchical skills.** A SKILL.md can reference other files in its folder — a `details.md` for edge cases, a `reference.md` for API specs. The agent reads them on demand, just like the SKILL.md itself.
- **Auto-installed skills.** Once a team has built a few skills, distributing them as a package or pulling them from a shared repo at agent startup beats copy-pasting folders.
- **Eval the descriptions.** Run a battery of user requests against your skill index and check which skill the model picks. A description that scores badly is the cheapest thing in the stack to fix.

## Skills or a tool?

You've now seen both halves of extending an agent — tools (including [MCP](../mcp/mcp.md) servers) in the previous lesson, and skills in this one. They're easy to conflate, but they answer different questions:

- A **tool** (a local function, or an MCP server) is *what the agent can do* — reach a system, call an API, query a database. Call it connectivity.
- A **skill** is *how the agent should do it* — which tool to use for a task, in what order, following which conventions. Call it knowledge.

So they aren't rivals; they stack. If you already have a working tool or MCP server, you've done the hard part — the skill is the layer on top that captures the workflow you already know, so the agent applies it consistently instead of re-deriving it every run. A skill might say "use the `notion_search` tool to find the design doc, then…" — `notion_search` is the capability; the skill is the recipe for using it well.

When you're unsure which you're missing *right now*, ask: is the agent unable to do the thing **at all** (it needs a tool), or able but doing it **badly** — wrong approach, wasted turns, ignorant of your conventions (it needs a skill)? Most real agents grow both.

## But what about RAG?

If you've worked with retrieval-augmented generation, skills will look familiar — both load context on demand instead of stuffing everything into the prompt. The difference is where the judgment lives.

In **RAG**, the system embeds the user's query, finds the top-k most similar chunks from a vector store, and pastes them into context. The retriever decides what's relevant, based on semantic similarity. The model just consumes the result.

In **skills**, the *model* decides what's relevant — reading descriptions, weighing them against the task, and choosing what to load. There's no embedding, no vector store, no top-k. Just a list of names and one-line summaries that the model reads like a menu.

This has consequences:

- **Skills compose with reasoning.** The model can read a skill, realize it needs *another* skill, and read that one too. RAG retrieves once per query.
- **Skills are auditable.** You can read the index and predict exactly which skills *could* be picked. Embedding-based retrieval is harder to introspect.
- **RAG scales to bigger corpora.** Once you have ten thousand documents, you can't list them all in the system prompt. RAG is the right tool. Skills work best in the 1–500 range — the regime where instructions and capabilities live, not raw documents.

The two combine well. A skill can *use* RAG ("to find similar past tickets, query the vector store at...") — instructions for retrieval, retrieving the data. Most mature agents end up with both.

## Further reading

- **[agentskills.io](https://agentskills.io)** — the open specification for the SKILL.md format, with a quickstart and a directory of agents that support it.
- **[Equipping agents for the real world with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)** — Anthropic's deep dive on progressive disclosure and why a filesystem beats a tool-per-task approach.
- **[anthropics/skills](https://github.com/anthropics/skills)** — Anthropic's reference repository of working skills. Read a few SKILL.md files end-to-end to see what good ones look like.
- **[The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)** (PDF) — Anthropic's longer guide, including the skills-vs-MCP "connectivity vs knowledge" framing this lesson borrows from.
- **[Cursor rules documentation](https://docs.cursor.com/context/rules)** — a similar (but always-loaded) take on file-based agent instructions, useful contrast.

Skills are how an agent stops being a stranger to your team and starts being a colleague. Each markdown file is a piece of institutional knowledge that no longer has to be re-explained in every conversation.

**Next:** [From a Message List to Memory](../memory/memory.md) — skills are knowledge you write *for* the agent; next, memory is knowledge the agent writes for itself.
