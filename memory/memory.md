# From a Message List to Memory: A Hands-On Intro

A short follow-on for developers who've built [an agent](../agents/agents.md) and noticed the uncomfortable truth from its very first lesson: the model is stateless, so *you* are the memory. By the end you'll have given an agent two kinds of memory — one that keeps a long conversation coherent, and one that lets it remember you across conversations.

We'll use OpenAI's API throughout. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of each idea clearly.

**Prerequisites:** Python 3.10+, an OpenAI API key in `OPENAI_API_KEY`, and `pip install openai`. Familiarity with the [agent loop](../agents/agents.md) helps but isn't required.

## Contents

1. [The Growing Message List](#part-1-the-growing-message-list)
2. [Trimming the Window](#part-2-trimming-the-window)
3. [Summarizing the Past](#part-3-summarizing-the-past)
4. [Memory on Disk](#part-4-memory-on-disk)
5. [A Memory Tool](#part-5-a-memory-tool)
6. [Recap](#recap)
7. [But what about RAG?](#but-what-about-rag)
8. [Further reading](#further-reading)

---

## Part 1: The Growing Message List

Recall the foundation from the agents course: the model has no memory, so you keep appending to a `messages` list and resend the whole thing every turn. That works — and it never stops growing.

```python
# growing_context.py
from openai import OpenAI

client = OpenAI()

messages = [{"role": "system", "content": "You are a helpful assistant."}]

for user_text in ["My name is Ada.", "I work on analytical engines.", "What's my name?"]:
    messages.append({"role": "user", "content": user_text})
    reply = client.chat.completions.create(model="gpt-5-mini", messages=messages)
    answer = reply.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    print(f"{len(messages):>2} messages in context -> {answer}")
# 3 messages in context -> Nice to meet you, Ada!
# 5 messages in context -> Analytical engines — wonderful.
# 7 messages in context -> Your name is Ada.
```

A few things to internalise:

- The only reason the model can answer "what's my name?" is that the full history — including turn one — is resent on every call. This is exactly the pattern from [agents.md Part 2](../agents/agents.md).
- The list only grows. Every exchange adds two messages, forever.
- You pay for the whole list on every turn, so a long conversation re-bills its early turns over and over. Eventually the list outgrows the model's **context window** and the call simply fails.

You need a way to forget.

## Part 2: Trimming the Window

The crudest way to bound context is a **sliding window**: always keep the system prompt, then only the last few messages.

```python
def trim(messages, keep=4):
    system = messages[:1]          # always keep the system prompt
    return system + messages[1:][-keep:]
```

Call `trim(messages)` before each request and the context can never overflow. Feed it our conversation from Part 1, though, and watch the bug:

```python
print(len(trim(messages)))          # bounded, no matter how long the chat runs
# 5

# But "My name is Ada." has scrolled out of the window.
# Ask "What's my name?" now and the model has nothing to go on:
# I'm not sure — you haven't told me your name yet.
```

A few things to internalise:

- Always keep the system prompt. Trimming it away strips the agent's standing instructions.
- A sliding window gives you predictable cost and a hard ceiling on context size.
- But it's lossy in the dumbest possible way — it forgets the *oldest* thing, which is often the *most important* thing (the user's name, the original task). It forgets by age, not by relevance.

We can do better than throwing old turns away.

## Part 3: Summarizing the Past

Instead of discarding old turns, fold them into a single summary message. This is **compaction**: drop the tokens, keep the information.

```python
def compact(messages, keep=4):
    system, rest = messages[:1], messages[1:]
    if len(rest) <= keep:
        return messages
    old, recent = rest[:-keep], rest[-keep:]

    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in old)
    summary = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{
            "role": "user",
            "content": f"Summarize this conversation, preserving names, "
                       f"facts, and decisions:\n\n{transcript}",
        }],
    ).choices[0].message.content

    note = {"role": "system", "content": f"Summary of earlier conversation:\n{summary}"}
    return system + [note] + recent
```

Now "what's my name?" survives even after the raw turn is gone, because the name was carried into the summary instead of dropped.

A few things to internalise:

- Compaction is lossy too — but lossy by *judgement* rather than by age. The model decides what's worth keeping.
- It costs an extra model call to produce the summary, but that cost is bounded and paid rarely.
- You choose *when* to compact: every N turns, or — better — when the context crosses a token budget. Real agents compact against a token count, not a message count.

This is short-term memory: it keeps a single conversation coherent. But a summary lives only as long as the program does. Close it and everything is forgotten. For memory that outlives the conversation, write it down.

## Part 4: Memory on Disk

Durable memory is just a file the agent reads at startup. It's the mirror image of a skill — in [skills.md](../skills/skills.md) the agent *reads* knowledge an author wrote; here the agent will *write* knowledge and read it back later.

```python
from pathlib import Path

MEMORY_FILE = Path("memory.md")

def load_memory():
    return MEMORY_FILE.read_text() if MEMORY_FILE.exists() else "(nothing yet)"

system_prompt = f"""You are a helpful assistant.

Here is what you remember about the user from past conversations:
{load_memory()}
"""
```

A few things to internalise:

- The file is loaded into the system prompt at startup — the same trick as the skill index in [skills.md Part 4](../skills/skills.md), just pointed the other way.
- Because the facts live *outside* the process, the agent now "remembers" across separate runs of your program.
- But so far *you* are still writing the file by hand. The last step is to let the agent maintain it.

## Part 5: A Memory Tool

Give the agent a tool to save facts and it can curate its own memory — deciding, mid-conversation, what's worth keeping. This is the agent loop from [agents.md Part 4](../agents/agents.md) with one extra tool.

```python
# memory_agent.py
from openai import OpenAI
from pathlib import Path
import json

client = OpenAI()
MEMORY_FILE = Path("memory.md")

def remember(fact):
    with MEMORY_FILE.open("a") as f:
        f.write(f"- {fact}\n")
    return f"Remembered: {fact}"

tools = [{
    "type": "function",
    "function": {
        "name": "remember",
        "description": "Save a durable fact about the user for future "
                       "conversations. Use for stable preferences, names, and "
                       "decisions — not for transient chatter.",
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string"}},
            "required": ["fact"],
        },
    },
}]

memory = MEMORY_FILE.read_text() if MEMORY_FILE.exists() else "(nothing yet)"
messages = [
    {"role": "system", "content": f"You are a helpful assistant. Save anything "
                                   f"worth remembering with the remember tool.\n\n"
                                   f"What you already remember:\n{memory}"},
    {"role": "user", "content": "I'm vegetarian and I always deploy on Fridays."},
]
print(f"user: {messages[1]['content']}\n")

# Standard agent loop — see ../agents/agents.md Part 4
while True:
    response = client.chat.completions.create(model="gpt-5-mini", messages=messages, tools=tools)
    msg = response.choices[0].message
    messages.append(msg)
    if not msg.tool_calls:
        print(f"\nagent: {msg.content}")
        break
    for call in msg.tool_calls:
        result = remember(**json.loads(call.function.arguments))
        print(result)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
# user: I'm vegetarian and I always deploy on Fridays.
# Remembered: User is vegetarian.
# Remembered: User deploys on Fridays.
#
# agent: Got it — noted that you're vegetarian and you deploy on Fridays.
```

A few things to internalise:

- The description does the work. Just like a skill description ([skills.md Part 6](../skills/skills.md)), it tells the model *when* to reach for the tool — and "not for transient chatter" is there to stop it saving noise.
- The agent now decides a fact is durable and writes it itself. Next run, those lines are in the system prompt.
- Append-only gets you far, but a complete set pairs `remember` with `forget` and `update` — otherwise memory grows stale and self-contradictory.

That's the whole picture. **Short-term memory** (compaction) keeps one conversation coherent; **long-term memory** (the file the agent writes) lets the agent improve across conversations.

## Recap

You've now built three things:

1. **A trimmed window** — context bounded by dropping the oldest turns. Cheap, and lossy by age.
2. **A compacted history** — old turns summarized in place. Short-term memory that survives within a conversation.
3. **A memory file the agent writes** — durable, long-term memory that survives across conversations.

That's enough to make an agent feel continuous. The next steps, once you want to go further:

- **Token-budget compaction.** Compact when context crosses a token threshold, not every N turns. Count tokens with `tiktoken` and trigger on the budget.
- **The selection problem.** Storing memories is easy; deciding *what* to store is the hard part. Too eager and memory fills with noise; too shy and it forgets what mattered. This is worth an eval.
- **Eviction and editing.** Add `forget` and `update`, or memory drifts stale and contradictory over time. A periodic "consolidation" pass that merges and prunes helps.
- **Structured memory.** A flat markdown file is fine to start. Graduate to one fact per record with metadata (when, why, confidence) once you need to update or query individual facts.
- **The Responses API.** OpenAI's newer API keeps conversation state on their servers, so you stop hand-managing the message list for short-term memory — the cost this course just made you feel. Worth learning once the pattern is clear.

## But what about RAG?

The skills course already introduced retrieval-augmented generation — and memory is where it comes back. Both load context on demand instead of stuffing everything into the prompt, so the line between them is worth drawing.

Everything in this course loads your *entire* memory: the whole message list, the whole summary, the whole file, pasted into the prompt every turn. That's perfect while memory is small. But once an agent has logged thousands of facts from months of conversations, you can't paste them all in — for the same reason you couldn't list ten thousand documents in a skill index ([skills.md's RAG note](../skills/skills.md) makes the same point).

At that scale, memory *becomes* a retrieval problem: embed each remembered fact, and at the start of a turn pull only the handful relevant to what the user just said. Compaction and the flat file load *everything you've kept*; RAG loads *only what's relevant right now*. They aren't rivals — RAG is simply what long-term memory turns into once it outgrows a file.

## Further reading

- **[OpenAI conversation state guide](https://platform.openai.com/docs/guides/conversation-state)** — how the Responses API keeps history server-side, the managed alternative to the message-list juggling in this course.
- **[tiktoken](https://github.com/openai/tiktoken)** — OpenAI's tokenizer. You need it the moment you want to compact against a token budget rather than a message count.
- **[MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)** — the paper that framed agent memory as a tiered hierarchy (in-context vs. external), with the model paging facts in and out itself. The conceptual backbone of Part 5.
- **[Letta](https://docs.letta.com)** — the open-source framework descended from MemGPT, if you'd rather adopt a memory system than hand-roll one.

An agent without memory meets you fresh every time. Memory is what turns a capable tool into one that knows you.

**Next:** [Bringing It All Together](../capstone/capstone.md) — the final lesson, where the loop, a sandboxed shell, tools, and memory become one runnable agent.
