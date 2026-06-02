# Bringing It All Together: A Minimal Agent

The other pieces in this repo each teach one idea in isolation. This one wires them into a single program you can actually talk to: a small interactive agent with a sandboxed shell, a few file tools, and a memory that survives between runs. It's the smallest honest sketch of a coding-style assistant — a stripped-down cousin of the agents people run in their terminals.

Unlike the tutorials, this isn't a type-along. The whole thing is in [agent.py](agent.py); read it top to bottom in one sitting (~220 lines, ~170 of them code) and this page explains how the parts fit.

It stays deliberately minimal: no auth, no streaming, no scheduling, error handling only where the loop would otherwise crash. The goal is to see how the concepts *compose*, not to ship it.

## What it ties together

Every piece traces back to one of the courses:

- **The agent loop** — call the model, run any tools it asks for, repeat until it stops. Straight from [agents.md Part 4](../agents/agents.md). Here it lives in `run_turn`.
- **A sandboxed shell** — one `bash` tool that runs inside a Docker container, never on your host. From [agents.md Part 6](../agents/agents.md). `curl`, `python`, `grep` and friends all come for free through it.
- **Convenience file tools** — `read_file` and `write_file` alongside `bash`, the "more base tools" suggested in the [agents recap](../agents/agents.md). The model writes shorter, clearer calls with them.
- **Short-term memory** — when the conversation grows past a threshold, `maybe_compact` summarizes the old turns into one note so context stays bounded. This is compaction from [memory.md Part 3](../memory/memory.md).
- **Long-term memory** — a `remember` tool appends durable facts to a file that's reloaded into the system prompt on the next run. From [memory.md Parts 4–5](../memory/memory.md).

The one course it *doesn't* fold in is [MCP](../mcp/mcp.md) — see [what's left out](#whats-deliberately-left-out) below.

## How it's wired

Three places hold state, and keeping them straight is the whole design:

```
your machine (host)                  Docker container
-------------------                  ----------------
agent.py        ── docker exec ──>   bash / read_file / write_file
agent_memory.md (the agent edits)    /workspace  (bind-mounted from /tmp/agent-work)
the message list (in memory)
```

- **The shell and file tools run in the container.** Anything the model does to the filesystem happens at `/workspace` inside the sandbox, which is bind-mounted to `/tmp/agent-work` on your host so you can inspect the results. Agent-generated commands never touch the rest of your machine.
- **Memory lives on the host, and you own it.** `remember` is a plain Python function that appends to `agent_memory.md` — it is *not* a sandbox command. The agent can write facts but can't reach outside `/workspace` to tamper with anything else. That separation is deliberate.
- **The message list is short-term and disposable.** It's compacted when long and thrown away when you quit. Only the memory file persists.

## The loop is the smallest part

Read [agent.py](agent.py) with this in mind: of its ~170 lines of code, the **loop** itself is about two dozen, and most of those are progress prints and safety rails. Strip them away and the whole loop is this:

```python
def run_turn(messages):
    while True:
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        ).choices[0].message
        messages.append(msg)

        if not msg.tool_calls:           # nothing requested -> the agent is done
            return msg.content

        for call in msg.tool_calls:      # otherwise run each tool, append results, loop
            args = json.loads(call.function.arguments)
            result = DISPATCH[call.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
```

That's the same loop from [agents.md Part 4](../agents/agents.md), unchanged. The `run_turn` in `agent.py` adds only three things to it, none of which alter its shape: an iteration cap (`for _ in range(25)` instead of `while True`), a line that prints each tool call so you can watch it work, and a `try/except` that feeds tool errors back to the model instead of crashing.

Everything else in the file is scaffolding *around* that loop:

- **the sandbox** — starting the container and mounting `/workspace` (~25 lines)
- **the tools** — four small functions, plus the JSON schemas that describe them to the model (the schemas alone are longer than the loop)
- **memory** — loading the file and compacting the transcript (~30 lines)
- **the REPL** — reading your input and printing replies (~18 lines)

All of that — the loop, the tools, the sandbox, the memory — is the **harness**: the program that runs the model. So `agent.py` *is* the harness; the model is what it runs; together, pointed at a goal, they're the agent (the vocabulary from [agents.md Part 4](../agents/agents.md)). The harness is small on purpose — the capability lives in the model deciding what to do; the code just runs the loop and carries the tools, sandbox, and memory along for the ride.

## Running it

You'll need Docker running, an OpenAI key, and the SDK:

```
export OPENAI_API_KEY=...
pip install openai
python agent.py
```

The first launch spends a few seconds starting the container and installing `curl` into it. After that the prompt appears.

## A session

```
agent ready — type a request, Ctrl-D to quit.

you> what's the weather in london today? celsius please
  · bash(curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.51&longitude=-0.13&current_weather=true&temperature_unit=celsius" -o /workspace/weather.json)
  · read_file(/workspace/weather.json)
  · remember(User prefers temperatures in Celsius.)

agent> Right now in London it's 24.6 °C, partly cloudy, wind 9 km/h. The raw
response is saved at /workspace/weather.json (on your host: /tmp/agent-work/).

you> ^D
bye.
```

One request touched everything: it reached the network through the shell (`curl`), wrote and read a file, and noticed a durable preference worth keeping (`remember`). That's the same `get_weather` example that opened the [agents](../agents/agents.md) and [MCP](../mcp/mcp.md) courses — except nobody wrote a weather tool this time. The agent fetched it itself with the one shell it has.

Now quit, restart, and ask about the weather somewhere else. The first thing it does on startup is reload `agent_memory.md` — so it gives you Celsius without asking. That round-trip, surviving a full restart, is the payoff of the whole series.

## What's deliberately left out

Each of these is a natural extension, and each already has a home in this repo:

- **MCP tools.** The agent's tools are all local functions. To use tools from an [MCP server](../mcp/mcp.md), the wiring is mechanical: take the schemas from the client's `list_tools()`, drop them into `TOOLS`, and forward matching calls to `client.call_tool()` instead of the local `DISPATCH`. The loop doesn't change.
- **Skills.** There's no `/skills` index here. Adding one is exactly the [skills course](../skills/skills.md): mount a skills folder into the container read-only, list the names and descriptions in the system prompt, and let the agent `cat` the relevant `SKILL.md` on demand.
- **Scheduling, multi-agent, auth, streaming.** Real assistants grow these. They're out of scope here on purpose — each would more than double the code.

## Where to take it next

- **Add the skills mount** to give the agent reusable, evolvable know-how on top of raw tools.
- **Connect an MCP server** so it can use tools you didn't write — the fastest way to make it genuinely capable.
- **Harden the sandbox.** Docker is fine for learning; decide what network access it gets, and look at microVMs for anything real.
- **Grow the memory.** Add `forget` and `update`, move from a flat file to one fact per record, and compact on a token budget rather than a message count — the next-steps from the [memory course](../memory/memory.md).

Strip away the production concerns and a useful agent is a short loop around a chat completion: tools to act, a sandbox to act safely, and memory so it doesn't meet you as a stranger every time. Everything else is engineering.
