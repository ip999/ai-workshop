# Lab 1 — From Completions to Agents

Build up a working agent from scratch, one piece at a time. Each lab is a short, self-contained step. The full written explanation for every step is in **[agents/agents.md](../../agents/agents.md)** — keep it open alongside this sheet.

**You'll need:** Python 3.10+, `pip install openai`, and an OpenAI API key:

```bash
export OPENAI_API_KEY=...        # get one at https://platform.openai.com/api-keys
```

Labs 1–4 need only Python. **Lab 5 needs Docker.** (Or run everything in the repo's [Codespace](../../README.md#run-it-in-the-browser-no-local-setup) — nothing to install.)

> Tip: each tutorial code block names the file to save it as (e.g. `# completion.py`). Use those names.

---

## Lab 1 — Your first completion

**Goal:** see that the model is stateless.

1. From [agents.md Part 1](../../agents/agents.md#part-1-a-completion), save the block as `completion.py`.
2. Run it: `python completion.py`.

✅ **Checkpoint:** it prints a one-line answer (e.g. `Paris.`).

🚀 **Stretch:** ask a follow-up like *"What's the population there?"* in a second call **without** resending the first turn. Watch it lose the thread — that's statelessness.

---

## Lab 2 — A multi-turn conversation

**Goal:** *be* the memory.

1. Save [Part 2](../../agents/agents.md#part-2-a-multi-turn-conversation) as `conversation.py` and run it.
2. Notice the second turn only works because you **resend the whole history**.

✅ **Checkpoint:** the model correctly answers "what's the population there?" — it resolved "there" from the history you sent.

🚀 **Stretch:** delete the line that appends the assistant reply, rerun, and see the answer degrade.

---

## Lab 3 — Add a tool

**Goal:** the model requests a call; you execute it.

1. Save [Part 3](../../agents/agents.md#part-3-adding-a-tool) as `weather_tool.py` (both code blocks — the second **continues** the same file).
2. Run it.

✅ **Checkpoint:** the first response has **no `content`** — it has `tool_calls`. After you run the tool and call again, you get the final sentence.

🚀 **Stretch:** add a second tool (e.g. `get_time(city)`) and ask a question that needs both.

---

## Lab 4 — The agent loop

**Goal:** turn "a model with tools" into an agent.

1. Save [Part 4](../../agents/agents.md#part-4-an-agent-the-loop) as `agent.py`.
2. Run it and ask: **"What's the weather in Paris and Tokyo?"**

✅ **Checkpoint:** the printed trace shows the model calling `get_weather` **twice**, the results going back, then a single final reply — and the loop exits.

🚀 **Stretch:** add `print()` lines (or a counter) to see exactly how many times the loop goes around.

---

## Lab 5 — An agent with a shell (Docker)

**Goal:** one general tool instead of many.

1. Start the sandbox (from [Part 6](../../agents/agents.md#part-6-an-agent-with-a-shell)):
   ```bash
   docker run -d --name agent-sandbox --rm -v /tmp/agent-work:/workspace \
       -w /workspace python:3.12-slim sleep infinity
   docker exec agent-sandbox bash -c "apt-get update -qq && apt-get install -y -qq curl"
   ```
2. Save the agent block as `shell_agent.py` and run it.
3. Ask: **"Create a file called hello.txt containing the first 10 prime numbers, one per line."**

✅ **Checkpoint:** watch the `$ command` lines as the agent writes and verifies the file. Confirm it on your host: `cat /tmp/agent-work/hello.txt`.

🚀 **Stretch:** ask it to fetch something with `curl` (e.g. the weather), or to count words in a file you drop into `/tmp/agent-work`.

---

## Wrap-up

You went from a single completion to an agent that can run shell commands in a sandbox. The loop never changed — you just gave it better tools.

**Next lesson:** [MCP](../../mcp/mcp.md) — where tools come from when you didn't write them.
