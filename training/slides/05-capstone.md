---
marp: true
theme: default
paginate: true
header: 'AI Workshop · Lesson 5'
footer: 'Bringing It All Together'
---

<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# Bringing It All Together

### Lesson 5 — the capstone

One runnable program that fuses everything: an interactive agent with a sandboxed shell, file tools, and memory that survives between runs.

---

## What an agent actually is

> **An LLM that runs tools in a loop to achieve a goal.**

- **tools** — it can act, not just talk.
- **in a loop** — it acts on feedback, step after step.
- **to achieve a goal** — there's a stopping condition.

Planning and memory aren't required — they *emerge* from the loop and *enhance* it. The capstone is exactly this definition, made real.

---

## What it ties together

- **The loop** — call the model, run its tools, repeat *(Lesson 1)*.
- **A sandboxed shell + file tools** — act safely in Docker *(Lesson 1)*.
- **Short- & long-term memory** — compaction + a file it writes *(Lesson 4)*.

The one piece left out is **MCP** *(Lesson 2)* — the tools here are local; wiring in an MCP server is mechanical.

---

## How it's wired

```
your machine (host)            Docker container
-------------------            ----------------
agent.py    ──exec──>          bash / read_file / write_file
agent_memory.md (host)         /workspace  (bind-mounted)
the message list (in memory)
```

Shell acts **only** inside the sandbox. Memory lives on the host — the agent can write facts, but can't reach outside `/workspace`.

---

## The loop is the smallest part

```python
def run_turn(messages):
    while True:
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS).choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            result = DISPATCH[call.function.name](**json.loads(call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
```

~12 lines. The rest of the file is sandbox, tools, and memory plumbing.

---

<!-- _class: lead -->

## 🧪 Your turn — run `agent.py`

Start it, ask for the weather, quit, restart — it still remembers.

→ "Running it" in [capstone.md](../../capstone/capstone.md)

---

## A session

```
you> what's the weather in london? celsius please
  · bash(curl -s "https://api.open-meteo.com/...&temperature_unit=celsius")
  · read_file(/workspace/weather.json)
  · remember(User prefers temperatures in Celsius.)
agent> Right now in London it's 24.6 °C, partly cloudy.
```

One request touched the shell, the network, a file, and memory — and nobody wrote a weather tool.

---

## What's deliberately left out

- **MCP tools** — wiring is mechanical: `list_tools()` → `TOOLS`, forward calls.
- **Skills** — add a `/skills` mount + index (Lesson 3).
- **Scheduling, multi-agent, auth, streaming** — out of scope on purpose.

Each is a natural extension with a home in the repo.

---

## The whole course, in one line

> An agent is a short **loop** around a chat completion: **tools** to act, a **sandbox** to act safely, and **memory** so it doesn't meet you as a stranger — running **to achieve a goal**.

Everything else is engineering.

📖 Full walk-through: [capstone/capstone.md](../../capstone/capstone.md)
