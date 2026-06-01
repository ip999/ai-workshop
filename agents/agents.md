# From Completions to Agents: A Hands-On Intro

A short course for developers who are new to LLM APIs. By the end you'll understand what an "agent" actually is, and you'll have built one that uses a sandboxed shell and a folder of skills to do work on its own.

We'll use OpenAI's API throughout. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of each idea clearly.

**Prerequisites:** Python 3.10+, an OpenAI API key in `OPENAI_API_KEY`, and `pip install openai`.

## Contents

1. [A Completion](#part-1-a-completion)
2. [A Multi-Turn Conversation](#part-2-a-multi-turn-conversation)
3. [Adding a Tool](#part-3-adding-a-tool)
4. [An Agent (the Loop)](#part-4-an-agent-the-loop)
5. [The Problem with Lots of Tools](#part-5-the-problem-with-lots-of-tools)
6. [An Agent with a Shell](#part-6-an-agent-with-a-shell)
7. [Skills](#part-7-skills)
8. [Recap](#recap)
9. [But what about MCP?](#but-what-about-mcp)
10. [Further reading](#further-reading)

---

## Part 1: A Completion

A completion is one round-trip. You send some text, the model sends some text back. That's it.

```python
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

## Part 2: A Multi-Turn Conversation

Since the model has no memory, *you* are the memory. To have a conversation, you keep appending to the `messages` list yourself.

```python
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

## Part 3: Adding a Tool

A completion can only produce text. But what if the model needs to do something — look up the weather, check a database, run some code? You give it **tools**.

A tool is just a Python function plus a JSON description of how to call it. The model never runs your code; it just emits a structured request saying "please call this function with these arguments." You run the function and send the result back.

```python
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

## Part 4: An Agent (the Loop)

Here's the insight that turns "a model with tools" into "an agent":

**What if the model wants to call multiple tools? Or call one tool, see the result, then call another based on what it learned?**

The answer is: don't ask the model just once. Put the whole thing in a loop. Keep calling the model until it stops requesting tools.

```python
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
    {"role": "system", "content": "You are an agent with access to a sandboxed Linux shell. Use the bash tool to accomplish tasks. The working directory is /workspace."},
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

## Part 7: Skills

A shell goes a long way, but the model still has to figure out *how* to do each task from scratch every time. "How do I extract text from a PDF in Python?" "What's the right `ffmpeg` invocation to trim a video?" It often gets these right, but it also often wastes turns trying wrong approaches.

**Skills** solve this. A skill is just a markdown file on disk that tells the agent how to do something. When the agent needs to do that thing, it reads the file and follows the instructions.

The agent doesn't load all skills into context. It sees only a short *index* — name and description — and reads the full skill on demand. This is the key trick: context stays small even with hundreds of skills available.

We'll keep skills on the host alongside our agent script, and bind-mount them into the container at `/skills` so the agent can `cat` and execute them via bash:

```
./skills/                    (on the host, next to your agent script)
  pdf/
    SKILL.md
    extract.py
  web-scrape/
    SKILL.md
```

Restart the sandbox container so both `/workspace` and `/skills` are mounted:

```bash
mkdir -p /tmp/agent-work ./skills
docker rm -f agent-sandbox 2>/dev/null
docker run -d --name agent-sandbox --rm \
    -v /tmp/agent-work:/workspace \
    -v "$(pwd)/skills:/skills:ro" \
    -w /workspace \
    python:3.12-slim sleep infinity

# Reinstall curl — restarting the container starts from the bare slim image again.
docker exec agent-sandbox bash -c "apt-get update -qq && apt-get install -y -qq curl"
```

A skill file (`./skills/pdf/SKILL.md`) looks like this:

````markdown
---
name: pdf
description: Use whenever the user wants to extract text from, merge, split, or fill PDF files.
---

# PDF skill

## Extracting text from a PDF

Run: `python /skills/pdf/extract.py <path-to-pdf>`

It prints the extracted text to stdout.

## Merging PDFs

Use pypdf:
```python
from pypdf import PdfWriter
writer = PdfWriter()
for path in input_paths:
    writer.append(path)
writer.write(output_path)
```
````

Note that the SKILL.md references `/skills/pdf/extract.py` — that's the path *inside the container*, which is what the agent will use when it calls `bash`. On the host, that same file lives at `./skills/pdf/extract.py`.

Now the agent. We build a skill index by reading the host directory, but the paths we emit into the prompt are the container-side `/skills/...` paths so the agent can actually use them.

```python
from openai import OpenAI
from pathlib import Path
import json
import subprocess
import re

client = OpenAI()

def bash(command):
    result = subprocess.run(
        ["docker", "exec", "agent-sandbox", "bash", "-c", command],
        capture_output=True, text=True, timeout=60,
    )
    return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

tools = [{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a bash command in the sandbox.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}]

# Read skills from the host filesystem, but emit container paths
# (the host's ./skills is mounted at /skills inside the container).
def build_skill_index(host_dir="./skills", container_dir="/skills"):
    lines = []
    for skill_md in Path(host_dir).glob("*/SKILL.md"):
        text = skill_md.read_text()
        name = re.search(r"^name:\s*(.+)$", text, re.M).group(1).strip()
        desc = re.search(r"^description:\s*(.+)$", text, re.M).group(1).strip()
        container_path = f"{container_dir}/{skill_md.parent.name}/SKILL.md"
        lines.append(f"- **{name}** (`{container_path}`): {desc}")
    return "\n".join(lines)

system_prompt = f"""You are an agent with a sandboxed Linux shell.

Your working directory is /workspace.

You also have a read-only /skills directory containing prewritten instructions for common tasks. Before starting a task, check this index and `cat` the relevant SKILL.md if one looks useful:

{build_skill_index()}

Use bash for everything. Be concise."""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Extract the text from /workspace/report.pdf and tell me how many times the word 'revenue' appears."},
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
        print(result[:500])
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })
```

What happens when you run this: the agent sees the skill index in its system prompt, with paths like `/skills/pdf/SKILL.md`. It notices the `pdf` skill matches the task, runs `cat /skills/pdf/SKILL.md`, learns about `extract.py`, runs `python /skills/pdf/extract.py /workspace/report.pdf`, then pipes the output through `grep -c revenue`. Done.

You just added a capability *without writing a single tool*. To add another (say, video editing), you make a folder, write a SKILL.md, maybe include a helper script. The agent picks it up on the next run.

Skills are a deep topic in their own right — writing descriptions that reliably trigger, bundling code, indexing hundreds of them. The [skills course](../skills/skills.md) covers all of it.

## Recap

You've now built three things:

1. **A completion** — one shot, no memory.
2. **A simple agent** — model + tools + a loop. Stop when the model stops calling tools.
3. **A capable agent** — model + a single shell tool + a folder of skills. New capabilities are markdown files, not code.

That's enough to build real things. The next steps, once you want to go further:

- **Better sandboxing.** Docker is fine for learning. Production agents use Firecracker microVMs or hosted services like E2B or Modal.
- **More base tools.** `read_file`, `write_file`, `edit_file`, `glob`, `grep` as conveniences alongside `bash`. The model writes shorter, clearer code with them.
- **Safety rails.** Cap iterations (`for _ in range(25)` instead of `while True`). Truncate large tool outputs. Decide what network access the sandbox gets. Wrap each tool call in try/except and feed the exception message back to the model as the tool result — it will often recover and try a different approach.
- **The Responses API.** OpenAI's newer API keeps conversation state on their servers and preserves reasoning across turns. Worth learning once you've felt the cost of resending history.
- **Real skills.** Skills get genuinely powerful when they encode tribal knowledge — "in our codebase, run tests with X", "our deployments work like Y". Each one is just a markdown file. See the [skills course](../skills/skills.md) for the full treatment.
- **Memory.** This agent forgets everything when the program exits, and its context grows without bound during a long session. The [memory course](../memory/memory.md) covers both — compaction for the conversation, a file on disk for what should outlive it.

## But what about MCP?

If you've been reading about agents recently, you've probably seen MCP — the Model Context Protocol — mentioned constantly. Here's how it fits into the picture we've built.

MCP is a standard for connecting agents to tools that live in a *separate process*. It slots into the **tools** layer (Parts 3 and 4) and answers the question "where do tools come from and who maintains them?"

Recall the tool we wrote in Part 3:

```python
def get_weather(city):
    return f"It's 18°C and cloudy in {city}."
```

A local Python function. With MCP, that same tool lives in a separate **MCP server** — its own process, possibly written by someone else, possibly running on a different machine. Your agent connects to the server, asks "what tools do you have?", gets back a list of JSON schemas, and from then on tool calls flow: model → your loop → MCP server → real implementation → result → back to the model.

From the model's perspective, **nothing changes**. It still sees tool schemas and emits tool calls. MCP is plumbing between your agent and the tool implementations.

**Why this matters:** before MCP, every agent framework had its own tool format. A nice "search Notion" integration written for LangChain couldn't be used in your custom agent without porting it. MCP standardises the interface so a tool can be written once and used by any MCP-compatible agent — Claude, the OpenAI Agents SDK, Cursor, Goose, your hand-rolled loop, whatever.

**MCP vs skills.** These get conflated because both "extend an agent," but they sit at different layers:

- **Tools (MCP or local) are *capabilities*** — what the agent can *do*. Run a query. Send a message. Read a file.
- **Skills are *instructions*** — how to *use* capabilities to accomplish a task.

A skill might say "use the `notion_search` tool to find the design doc, then..." — and `notion_search` could be coming from an MCP server. The skill teaches the workflow; MCP provides the underlying tool. Most real agents end up with both.

**Which do you reach for?** Ask whether the agent is missing an *ability* or missing *know-how*:

- It **can't do the thing at all** — reach a system it has no access to, call an API behind auth, query a private database → it needs a **tool** (a local function, or an MCP server if you want that tool reusable across agents or maintained by someone else).
- It **can already do the thing but does it badly** — picks the wrong library, wastes turns, doesn't know your team's conventions → it needs a **skill**.

Adding a `bash` tool gave our agent a huge range of new abilities at once; a skill then teaches it to use them well. That's why most agents grow both — and why a new capability is sometimes code and sometimes just a markdown file.

We didn't introduce MCP earlier because it's a deployment and distribution concern, not a conceptual one — the mental model of "tools are just functions" is more important to nail first. Once you've built a few agents and start wanting tools you didn't write yourself, MCP is a natural next step — the [MCP course](../mcp/mcp.md) walks you from a plain function to a server any agent can connect to.

## Further reading

The skills pattern shown here is now an open standard with a growing ecosystem of supporting tools.

- **[agentskills.io](https://agentskills.io)** — the canonical open specification for the SKILL.md format. Covers the spec, a quickstart, and a directory of compatible agents (Claude Code, Cursor, Goose, OpenCode, Gemini CLI, and many more).
- **[Equipping agents for the real world with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)** — Anthropic's engineering deep-dive on the design philosophy behind skills, including progressive disclosure and why a filesystem beats a tool-per-task approach.
- **[anthropics/skills](https://github.com/anthropics/skills)** — Anthropic's reference repository of real, working skills. Worth reading a few SKILL.md files end-to-end to see what good ones look like.
- **[OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)** — the official reference for the tool-use API we used throughout this course, including more advanced features like parallel tool calls and structured outputs.
- **[modelcontextprotocol.io](https://modelcontextprotocol.io)** — the official MCP specification, with quickstarts for building your own MCP server in Python or TypeScript.

The whole thing — the entire idea of "an agent" — is a loop around a chat completion with tools. Once that clicks, the rest is engineering.
