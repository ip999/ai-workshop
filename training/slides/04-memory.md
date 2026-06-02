---
marp: true
theme: default
paginate: true
header: 'AI Workshop · Lesson 4'
footer: 'From a Message List to Memory'
---

<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# From a Message List to Memory

### Lesson 4 — state that survives

The model is stateless, so *you* are the memory. Two kinds: one that keeps a long conversation coherent, one that remembers you across conversations.

---

## The whole idea, up front

> Short-term memory keeps a conversation coherent; long-term memory makes the agent improve across them.

The running message list is already working memory. Everything here is managing it.

**Today:**
1 the growing list → 2 trimming → 3 compaction → 4 memory on disk → 5 a memory tool

---

## Part 1 — The Growing Message List

You append every turn and resend the whole list. It only grows.

```python
messages.append({"role": "user", "content": user_text})
# ... resend EVERYTHING every turn
```

You re-bill early turns over and over, and eventually overflow the **context window**. You need a way to forget.

---

<!-- _class: lead -->

## 🧪 Your turn — `growing_context.py`

Watch the message count climb while the model still recalls your name.

→ exercise at the end of **Part 1** in [memory.md](../../memory/memory.md)

---

## Part 2 — Trimming the Window

The crudest fix: keep the system prompt + the last few messages.

```python
def trim(messages, keep=4):
    return messages[:1] + messages[1:][-keep:]
```

Bounded context — but lossy in the dumbest way: it forgets the **oldest** thing, which is often the most important (your name, the original task).

---

<!-- _class: lead -->

## 🧪 Your turn — add `trim()`

Bound the context, then watch the model forget your name once it scrolls off.

→ exercise at the end of **Part 2**

---

## Part 3 — Summarizing the Past

Don't discard old turns — **compact** them into one summary. Drop the tokens, keep the information.

```python
note = {"role": "system", "content": f"Summary so far:\n{summary}"}
return system + [note] + recent
```

Lossy by *judgement*, not by age. This is **short-term memory** — coherent within a conversation, gone when the program exits.

---

## Part 4 — Memory on Disk

Durable memory is just a file the agent reads at startup.

```python
system_prompt = f"What you remember:\n{load_memory()}"
```

It's the **mirror image of a skill**: a skill is knowledge you *read*; memory is knowledge the agent *writes* and reads back.

---

## Part 5 — A Memory Tool

Give the agent a `remember` tool and it curates its own memory.

```python
@tool
def remember(fact):
    MEMORY_FILE.open("a").write(f"- {fact}\n")
```

The description does the work: "save durable facts — not transient chatter."

---

<!-- _class: lead -->

## 🧪 Your turn — `memory_agent.py`

Run it, then **run it again** — the second run already knows you.

→ exercise at the end of **Part 5**

---

## Recap

You built three things:

1. **A trimmed window** — bounded, lossy by age.
2. **A compacted history** — short-term memory, summarized in place.
3. **A memory file** — long-term memory the agent writes, surviving restarts.

Short-term keeps a conversation coherent; long-term makes the agent improve across them.

---

## But what about RAG?

Everything here loads your *entire* memory into the prompt. Fine while it's small.

Once an agent has logged thousands of facts, you can't paste them all in — you **retrieve** only what's relevant now. Memory at scale *becomes* a retrieval problem.

---

## Next: bring it all together

Loop + tools + a sandbox + memory — in one runnable program.

That's the **capstone** — Lesson 5.

📖 Full walk-through: [memory/memory.md](../../memory/memory.md)
