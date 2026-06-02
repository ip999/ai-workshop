# From Completions to Agents: A Hands-On Intro

A short course for developers who are new to LLM APIs — the first lesson of this workshop. By the end you'll understand what an "agent" actually is, and you'll have built one that uses a sandboxed shell to do work on its own.

We'll use OpenAI's API throughout. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of each idea clearly.

**Prerequisites:** Python 3.10+, an OpenAI API key in `OPENAI_API_KEY` (create one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)), and `pip install openai`.

## Contents

1. [A Completion](#part-1-a-completion)
2. [A Multi-Turn Conversation](#part-2-a-multi-turn-conversation)
3. [Adding a Tool](#part-3-adding-a-tool)
4. [An Agent (the Loop)](#part-4-an-agent-the-loop)
5. [The Problem with Lots of Tools](#part-5-the-problem-with-lots-of-tools)
6. [An Agent with a Shell](#part-6-an-agent-with-a-shell)
7. [Recap](#recap)
8. [Next: tools you didn't write](#next-tools-you-didnt-write)
9. [Further reading](#further-reading)

---

## Part 1: A Completion

A completion is one round-trip. You send some text, the model sends some text back. That's it.

```python
# completion.py
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "user", "content": "What's the capital of France?"}
    ],
)

print(response.choices[0].message.content)
# Paris.
```

A few things to internalise:

- The model is **stateless**. It has no memory between calls. If you ask a follow-up, you have to send the previous turns again.
- `messages` is a list of `{"role": ..., "content": ...}` dicts. Roles are `system` (instructions), `user` (you), and `assistant` (the model).
- The response object has a lot of fields. For now we only care about `.choices[0].message.content`.

> **🧪 Your turn** — save the block above as `completion.py` and run it.
>
> - ✅ It prints a one-line answer (e.g. `Paris.`).
> - 🚀 Ask a follow-up in a second call *without* resending the first turn — watch it lose the thread. That's statelessness.

## Part 2: A Multi-Turn Conversation

Since the model has no memory, *you* are the memory. To have a conversation, you keep appending to the `messages` list yourself.

```python
# conversation.py
from openai import OpenAI

client = OpenAI()

messages = [
    {"role": "user", "content": "What's the capital of France?"}
]

# First turn
response = client.chat.completions.create(model="gpt-5-mini", messages=messages)
reply = response.choices[0].message.content
print("Assistant:", reply)
messages.append({"role": "assistant", "content": reply})

# Second turn — note we send the entire history
messages.append({"role": "user", "content": "What's the population there?"})
response = client.chat.completions.create(model="gpt-5-mini", messages=messages)
print("Assistant:", response.choices[0].message.content)
```

The model can answer "what's the population there?" only because we sent the full prior conversation. Drop the history and it has no idea what "there" refers to.

This is the foundation. Everything else in this course is built on top of this pattern.

> **🧪 Your turn** — save this as `conversation.py` and run it.
>
> - ✅ The model answers "what's the population there?" — it resolved "there" from the history you sent.
> - 🚀 Delete the line that appends the assistant reply, rerun, and watch the answer degrade.

## Part 3: Adding a Tool

A completion can only produce text. But what if the model needs to do something — look up the weather, check a database, run some code? You give it **tools**.

A tool is just a Python function plus a JSON description of how to call it. The model never runs your code; it just emits a structured request saying "please call this function with these arguments." You run the function and send the result back.

```python
# weather_tool.py
from openai import OpenAI
import json

client = OpenAI()

# 1. The actual function
def get_weather(city):
    # Pretend this hits a real API
    return f"It's 18°C and cloudy in {city}."

# 2. Describe it for the model
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"],
        },
    },
}]

# 3. Ask a question that needs the tool
messages = [{"role": "user", "content": "What's the weather in Paris?"}]

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=messages,
    tools=tools,
)

msg = response.choices[0].message
print(msg)
# ChatCompletionMessage(content=None, tool_calls=[ChatCompletionMessageToolCall(
#   id='call_abc123', function=Function(arguments='{"city":"Paris"}', name='get_weather'))])
```

Notice the model didn't answer. Instead of `content`, the response has `tool_calls` — a request to run `get_weather(city="Paris")`. We have to actually run it ourselves, then send the result back as a new message.

```python
# weather_tool.py (continued)
# Append the model's tool-call message to history
messages.append(msg)

# Run each requested tool
for call in msg.tool_calls:
    args = json.loads(call.function.arguments)
    result = get_weather(**args)
    messages.append({
        "role": "tool",
        "tool_call_id": call.id,
        "content": result,
    })

# Ask the model again, now with the tool result in history
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=messages,
    tools=tools,
)

print(response.choices[0].message.content)
# It's currently 18°C and cloudy in Paris.
```

That's the full picture: ask → model requests tool → you run tool → send result → model answers.

> **🧪 Your turn** — save both blocks as `weather_tool.py` (the second continues the file) and run it.
>
> - ✅ The first response has no `content` — only `tool_calls`. After you run the tool and call again, you get the final sentence.
> - 🚀 Add a second tool (e.g. `get_time(city)`) and ask a question that needs both.

## Part 4: An Agent (the Loop)

Here's the insight that turns "a model with tools" into "an agent":

**What if the model wants to call multiple tools? Or call one tool, see the result, then call another based on what it learned?**

The answer is: don't ask the model just once. Put the whole thing in a loop. Keep calling the model until it stops requesting tools.

```python
# agent.py
from openai import OpenAI
import json

client = OpenAI()

def get_weather(city):
    return f"It's 18°C and cloudy in {city}."

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]

messages = [{"role": "user", "content": "What's the weather in Paris and Tokyo?"}]
print(f"user: {messages[0]['content']}")

# THE AGENT LOOP
while True:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        tools=tools,
    )
    msg = response.choices[0].message
    messages.append(msg)

    # If the model is done calling tools, it produced a normal reply. Exit.
    if not msg.tool_calls:
        print(msg.content)
        break

    # Otherwise, run each tool call and append the results, then loop.
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        print(f"→ model wants: {call.function.name}({args})")
        result = get_weather(**args)
        print(f"← tool result: {result}")
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })
```

Run it and you can watch the round-trip the prose below describes:

```
# user: What's the weather in Paris and Tokyo?
# → model wants: get_weather({'city': 'Paris'})
# ← tool result: It's 18°C and cloudy in Paris.
# → model wants: get_weather({'city': 'Tokyo'})
# ← tool result: It's 18°C and cloudy in Tokyo.
# It's 18°C and cloudy in both Paris and Tokyo.
```

That's an agent. The model called `get_weather` twice (once for Paris, once for Tokyo), saw both results, then wrote a final reply. The loop exits because the final reply has no tool calls.

**This is the entire pattern.** Everything else — coding agents, research agents, customer support agents — is just this loop with different tools.

> **🧪 Your turn** — save this as `agent.py` and ask: *"What's the weather in Paris and Tokyo?"*
>
> - ✅ The trace shows `get_weather` called twice, the results going back, then one final reply — and the loop exits.
> - 🚀 Add a counter to see how many times the loop goes around.

## Part 5: The Problem with Lots of Tools

Once you've seen the loop, the temptation is to add more tools. Want to read a PDF? Add a `read_pdf` tool. Send an email? `send_email`. Resize an image? `resize_image`.

Pretty soon you have a problem:

```python
tools = [
    {"type": "function", "function": {"name": "read_pdf", ...}},
    {"type": "function", "function": {"name": "extract_pdf_text", ...}},
    {"type": "function", "function": {"name": "merge_pdfs", ...}},
    {"type": "function", "function": {"name": "send_email", ...}},
    {"type": "function", "function": {"name": "read_email", ...}},
    {"type": "function", "function": {"name": "resize_image", ...}},
    {"type": "function", "function": {"name": "convert_image", ...}},
    # ...30 more
]
```

Every tool definition goes into the prompt on every turn. Context bloats. The model gets confused about which tool to use. Adding a new capability means writing new code, new schemas, new tests, redeploying.

There's a better way.

## Part 6: An Agent with a Shell

Instead of a tool for every task, give the agent **one general tool**: a sandboxed shell. Now it can do anything bash can do — which is almost anything.

First, the sandbox. **Never run agent-generated commands directly on your machine.** We'll use Docker.

```bash
# Create a working directory on the host, then start a long-running container
# with that directory bind-mounted at /workspace inside the container.
mkdir -p /tmp/agent-work
docker run -d --name agent-sandbox --rm \
    -v /tmp/agent-work:/workspace \
    -w /workspace \
    python:3.12-slim sleep infinity

# The slim image has no curl; install it so the agent can fetch from the web.
docker exec agent-sandbox bash -c "apt-get update -qq && apt-get install -y -qq curl"
```

Now the agent loop, with a single `bash` tool:

```python
# shell_agent.py
from openai import OpenAI
import json
import subprocess

client = OpenAI()

def bash(command):
    """Run a shell command in the sandbox container and return its output."""
    result = subprocess.run(
        ["docker", "exec", "agent-sandbox", "bash", "-c", command],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

tools = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a bash command in a sandboxed Linux container. Use this for any task involving files, code, or shell utilities.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}]

messages = [
    {"role": "system", "content": (
        "You are an agent with access to a sandboxed Linux shell. "
        "Use the bash tool to accomplish tasks. "
        "The working directory is /workspace."
    )},
    {"role": "user", "content": "Create a file called hello.txt containing the first 10 prime numbers, one per line."},
]
print(f"user: {messages[1]['content']}\n")

while True:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        tools=tools,
    )
    msg = response.choices[0].message
    messages.append(msg)

    if not msg.tool_calls:
        print(f"\nagent: {msg.content}")
        break

    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        result = bash(**args)
        print(f"$ {args['command']}")
        print(result)
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })
```

Run this and watch what happens. The model will probably write a small Python snippet to generate primes, pipe the output into `hello.txt`, then verify with `cat`. With one tool, it can do an enormous range of things.

This is closer to how real coding agents work. Pair this `bash` tool with `read_file`, `write_file`, and `edit_file` (also implemented as small functions calling `docker exec`) and you have the core of a capable agent in under 100 lines.

> **🧪 Your turn** — start the sandbox (above), save the agent as `shell_agent.py`, and ask it to create `hello.txt` with the first 10 prime numbers.
>
> - ✅ Watch the `$ command` lines as it writes and verifies the file; confirm on your host with `cat /tmp/agent-work/hello.txt`.
> - 🚀 Ask it to fetch something with `curl`, or to count words in a file you drop into `/tmp/agent-work`.

## Recap

You've now built three things:

1. **A completion** — one shot, no memory.
2. **A simple agent** — model + tools + a loop. Stop when the model stops calling tools.
3. **A capable agent** — model + a single shell tool. One tool, an enormous range of tasks.

That's enough to build real things. A few refinements to the loop itself, once you want to go further:

- **Better sandboxing.** Docker is fine for learning. Production agents use Firecracker microVMs or hosted services like E2B or Modal.
- **More base tools.** `read_file`, `write_file`, `edit_file`, `glob`, `grep` as conveniences alongside `bash`. The model writes shorter, clearer code with them.
- **Safety rails.** Cap iterations (`for _ in range(25)` instead of `while True`). Truncate large tool outputs. Decide what network access the sandbox gets. Wrap each tool call in try/except and feed the exception message back to the model as the tool result — it will often recover and try a different approach.
- **The Responses API.** OpenAI's newer API keeps conversation state on their servers and preserves reasoning across turns. Worth learning once you've felt the cost of resending history.

## Next: tools you didn't write

You wrote `get_weather` yourself, as a local Python function. A lot of the time, though, you'll want tools you *didn't* write — ones that talk to a database, a SaaS API, or your company's internal systems, often living in a separate process and maintained by someone else.

Standardising that is what **MCP** (the Model Context Protocol) does, and it's the next lesson. From the model's perspective nothing changes — it still sees tool schemas and emits tool calls — but the implementations now live behind a standard interface any agent can connect to.

**Next:** [From a Function to an MCP Server](../mcp/mcp.md) — wrap a tool so any agent can use it.

## Further reading

- **[OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)** — the official reference for the tool-use API we used throughout this lesson, including parallel tool calls and structured outputs.
- **[Anthropic's MCP announcement](https://www.anthropic.com/news/model-context-protocol)** — background on the protocol the next lesson builds on.

The whole thing — the entire idea of "an agent" — is a loop around a chat completion with tools, running to achieve a goal. Once that clicks, the rest is engineering.
