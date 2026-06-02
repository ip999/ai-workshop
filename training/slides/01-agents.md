---
marp: true
theme: default
paginate: true
header: 'AI Workshop · Lesson 1'
footer: 'From Completions to Agents'
---

<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# From Completions to Agents

### Lesson 1 — what an "agent" actually is

A model, some tools, and a loop. By the end you'll have built one that drives a sandboxed shell.

---

## The whole idea, up front

> An agent is a **loop around a chat completion with tools**.

Everything else — coding agents, research agents, support bots — is this loop with different tools.

**Today** — we present a part, then you build it (six parts, five exercises):

1 completion → 2 conversation → 3 a tool → **4 the loop** → 5 too many tools → **6 a shell**

---

## Part 1 — A Completion

One round-trip: text in, text out.

```python
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": "Capital of France?"}],
)
print(response.choices[0].message.content)   # Paris.
```

- The model is **stateless** — no memory between calls.
- `messages` is a list of `{role, content}`: `system`, `user`, `assistant`.

---

<!-- _class: lead -->

## 🧪 Your turn — `completion.py`

Run your first completion and confirm the model has no memory.

→ exercise at the end of **Part 1** in [agents.md](../../agents/agents.md)

---

## Part 2 — A Multi-Turn Conversation

The model forgets, so **you are the memory**: keep appending to `messages` and resend the whole list every turn.

```python
messages.append({"role": "assistant", "content": reply})
messages.append({"role": "user", "content": "What's the population there?"})
# resend the ENTIRE history — that's the only reason "there" resolves
```

This is the foundation everything else builds on.

---

<!-- _class: lead -->

## 🧪 Your turn — `conversation.py`

Resend the whole history and watch *"there"* resolve.

→ exercise at the end of **Part 2**

---

## Part 3 — Adding a Tool

A tool is a **function + a JSON description**. The model never runs your code — it emits a *request* to call it. You run it and send the result back.

```python
tools = [{"type": "function", "function": {
    "name": "get_weather", "description": "Get the weather for a city",
    "parameters": {"type": "object",
        "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
```

Response has `tool_calls` instead of `content` → run it → append a `{"role": "tool", ...}` message → ask again.

---

<!-- _class: lead -->

## 🧪 Your turn — `weather_tool.py`

The first response has `tool_calls`, **not** `content`. Run the tool, call again.

→ exercise at the end of **Part 3**

---

## Part 4 — An Agent (the Loop)

Don't ask once. **Loop** until the model stops asking for tools.

```python
while True:
    msg = client.chat.completions.create(
        model="gpt-5-mini", messages=messages, tools=tools).choices[0].message
    messages.append(msg)
    if not msg.tool_calls:          # normal reply -> done
        print(msg.content); break
    for call in msg.tool_calls:     # run each tool, append results, loop
        result = run(call)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
```

**This is the entire pattern.**

---

<!-- _class: lead -->

## 🧪 Your turn — `agent.py`

Ask: *"weather in Paris and Tokyo?"* — watch it call the tool twice, then reply.

→ exercise at the end of **Part 4**

---

## Part 5 — The Problem with Lots of Tools

Add a tool per task — `read_pdf`, `send_email`, `resize_image`, … 30 more — and:

- Every schema is in the prompt **every turn** → context bloats.
- The model gets **confused** about which to use.
- New capability = new code, schema, tests, redeploy.

There's a better way. *(No lab here — this is the motivation for the shell.)*

---

## Part 6 — An Agent with a Shell

Give the agent **one general tool**: a sandboxed shell. Now it can do almost anything `bash` can.

> ⚠️ **Never run agent-generated commands on your machine.** Use Docker.

```python
def bash(command):
    return subprocess.run(["docker", "exec", "agent-sandbox",
        "bash", "-c", command], capture_output=True, text=True).stdout
```

One tool, an enormous range of tasks — the core of a real coding agent.

---

<!-- _class: lead -->

## 🧪 Your turn — `shell_agent.py`

Start the Docker sandbox, then ask the agent to write a file of prime numbers.

→ exercise at the end of **Part 6**

---

## Recap

You built three things:

1. **A completion** — one shot, no memory.
2. **A simple agent** — model + tools + a loop.
3. **A capable agent** — model + one shell tool.

The intelligence is in the **model**; your code just runs the loop and carries the tools.

---

## Next: tools you didn't write

You wrote `get_weather` yourself. Real agents use tools they *didn't* write — in another process, maintained by someone else.

That's **MCP**, and it's Lesson 2.

📖 Full walk-through: [agents/agents.md](../../agents/agents.md)
