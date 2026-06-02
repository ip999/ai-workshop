---
marp: true
theme: default
paginate: true
header: 'AI Workshop · Lesson 3'
footer: 'From a System Prompt to a Skill'
---

<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# From a System Prompt to a Skill

### Lesson 3 — durable, reusable know-how

Tools (Lesson 2) give the agent *abilities*. Skills give it the *knowledge* of how to use them well — loaded from disk, on demand.

---

## The whole idea, up front

> A skill is the **knowledge** layer — *how* the agent should do something.

Instructions (and code) in a file the agent reads only when relevant.

**Today:**
1 a system prompt → 2 a long one → 3 a skill on disk → 4 the skill index → 5 skills that ship code → 6 a description that triggers

---

## Part 1 — A System Prompt

The simplest place to put instructions: the system prompt.

```python
messages=[
  {"role": "system", "content": "When summarizing CSVs, report row count, columns, and one example row."},
  {"role": "user", "content": "Summarize this CSV: ..."},
]
```

Fine for a sentence or two. Every token is paid for on **every** call.

---

<!-- _class: lead -->

## 🧪 Your turn — `describe_csv.py`

Run the system-prompt demo; watch the model follow the format.

→ exercise at the end of **Part 1** in [skills.md](../../skills/skills.md)

---

## Part 2 — A Long System Prompt

Now make it know CSVs *and* PDFs *and* git *and* deploys *and* expenses…

- The prompt bloats — you pay for PDF rules even when asked about CSVs.
- The model filters relevant guidance out of a wall of text → accuracy drops.
- A new domain means editing one monolith and re-shipping.

There's a better way.

---

## Part 3 — A Skill on Disk

Put the instructions in a file; give the agent a tool to read it when relevant.

```
skills/csv/SKILL.md
```

Better — but the agent has to *know the skill exists*. Naming every skill in the prompt is the same bloat problem again.

---

## Part 4 — The Skill Index

Keep only **names + descriptions** in the prompt; load the full file on demand.

```markdown
---
name: csv
description: Use when the user wants to summarize or analyze a CSV.
---
```

**The leap (progressive disclosure):** context stays small even with hundreds of skills, because the *model* decides what to load.

---

## Part 5 — Skills That Ship Code

A skill is a **folder**, not a file — bundle scripts alongside the instructions.

```
skills/csv/
├── SKILL.md        # how to use it
└── summarize.py    # the hard part, solved once
```

**Frozen expertise:** the trial-and-error you'd otherwise repeat every time, packaged so the agent gets it right first try.

---

<!-- _class: lead -->

## 🧪 Your turn — build the `csv` skill

Create `skills/csv/` with `SKILL.md` + `summarize.py` and run it.

→ exercise at the end of **Part 5**

---

## Part 6 — A Description That Triggers

The description is the only part the model sees by default — it decides whether the skill is used at all.

```yaml
# Bad
description: CSV utilities.
# Good
description: Use when the user wants to summarize, filter, or analyze a
  CSV, TSV, or delimited file. Covers delimiter detection and stats.
```

Lead with **"Use when…"**, include synonyms, don't oversell.

---

## Recap

You built three things:

1. **A system prompt** — instructions in context. Breaks down at scale.
2. **A skill on disk** — read on demand, but must be discovered.
3. **An indexed skills folder** — names in context, full content by judgment.

Add a capability by dropping in a folder. No code change.

---

## Skills or a tool?

Is the agent missing an **ability** or **know-how**?

- Can't do it at all → it needs a **tool** (local, or an MCP server).
- Does it badly → it needs a **skill**.

Tools are *what*; skills are *how*. A skill often *uses* a tool. Most agents grow both.

---

## But what about RAG?

Both load context on demand — the difference is **who decides**:

- **RAG:** a retriever picks top-k chunks by similarity.
- **Skills:** the *model* reads descriptions and chooses.

Skills shine in the 1–500 range; RAG scales to huge corpora. They combine.

---

## Next: state that survives

Skills are knowledge you write *for* the agent. Next, the agent writes knowledge *for itself* — and remembers across the conversation and beyond.

That's **Memory** — Lesson 4.

📖 Full walk-through: [skills/skills.md](../../skills/skills.md)
