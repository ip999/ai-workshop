# From a Function to an MCP Server: A Hands-On Intro

A short follow-on for developers who've built [an agent](../agents/agents.md) and now want to expose tools to it — and to other agents — over MCP. By the end you'll have written an MCP server that any MCP-compatible agent (Claude, Cursor, your hand-rolled loop) can connect to.

We'll use FastMCP throughout. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of each idea clearly.

**Prerequisites:** Python 3.10+, and `pip install fastapi uvicorn fastmcp httpx`.

## Contents

1. [A Function](#part-1-a-function)
2. [The Same Function as an HTTP API (FastAPI)](#part-2-the-same-function-as-an-http-api-fastapi)
3. [The Same Function as an MCP Server (FastMCP)](#part-3-the-same-function-as-an-mcp-server-fastmcp)
4. [Calling a Real API](#part-4-calling-a-real-api)
5. [More Than One Tool](#part-5-more-than-one-tool)
6. [Connecting an Agent](#part-6-connecting-an-agent)
7. [Recap](#recap)
8. [But what about resources and prompts?](#but-what-about-resources-and-prompts)
9. [Further reading](#further-reading)

---

## Part 1: A Function

A function is one input, one output. You call it, you get a result. That's it.

```python
def get_weather(city):
    return f"It's 18°C and cloudy in {city}."

print(get_weather("Paris"))
# It's 18°C and cloudy in Paris.
```

A few things to internalise:

- This is **a local function**. Only the code running in this Python process can call it.
- There's no protocol, no contract, no schema. The "interface" is whatever Python conventions you and the caller happen to agree on.
- To use it from another machine — or another language — you'd have to wrap it in something that speaks over a network.

## Part 2: The Same Function as an HTTP API (FastAPI)

The most common way to expose a function over a network is HTTP. FastAPI lets you do this with a single decorator.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/weather")
def get_weather(city: str):
    return f"It's 18°C and cloudy in {city}."
```

Save as `weather_api.py` and run:

```
uvicorn weather_api:app --port 8000
```

Now anyone with an HTTP client can call it:

```
curl "http://localhost:8000/weather?city=Paris"
# "It's 18°C and cloudy in Paris."
```

A few things to internalise:

- The function is the same. The decorator turns it into an endpoint.
- FastAPI inspects the type hints (`city: str`) and uses them to validate the request and generate an OpenAPI schema at `/openapi.json`.
- An *agent* could call this — but only if you also teach it the URL, the query-string format, and the response shape. There's no standard way for an agent to discover what endpoints a FastAPI app exposes.

That last point is the gap MCP fills.

## Part 3: The Same Function as an MCP Server (FastMCP)

MCP — Model Context Protocol — is a standard for exposing tools to agents. FastMCP is to MCP roughly what FastAPI is to HTTP: a decorator-driven library that wraps your functions.

```python
from fastmcp import FastMCP

mcp = FastMCP("weather")

@mcp.tool
def get_weather(city: str) -> str:
    return f"It's 18°C and cloudy in {city}."

if __name__ == "__main__":
    mcp.run()
```

Save as `weather_mcp.py` and run:

```
python weather_mcp.py
```

By default the server speaks over **stdio** — it reads MCP messages from stdin and writes them to stdout. That's the transport most local MCP servers use; the agent launches them as a subprocess and talks to them through pipes.

Compare the two side by side:

```python
# FastAPI                              # FastMCP
from fastapi import FastAPI            from fastmcp import FastMCP

app = FastAPI()                        mcp = FastMCP("weather")

@app.get("/weather")                   @mcp.tool
def get_weather(city: str):            def get_weather(city: str) -> str:
    return ...                             return ...
```

The function is identical. The decorator changed. **That's the whole conceptual leap.**

What did FastMCP do that FastAPI didn't? It made the tool *discoverable in a way agents understand*. Any MCP-compatible agent can connect to this server and ask "what tools do you have?" and get back a structured list of names, descriptions, and JSON schemas — without you writing any of that yourself. The model on the other end gets exactly the tool definitions it needs to start calling them.

## Part 4: Calling a Real API

A hardcoded weather string isn't very useful. Let's swap in a real one. [wttr.in](https://wttr.in) is a free weather service that takes a city in the URL and returns a one-line summary.

```python
from fastmcp import FastMCP
import httpx

mcp = FastMCP("weather")

@mcp.tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    response = httpx.get(f"https://wttr.in/{city}?format=3")
    return response.text.strip()

if __name__ == "__main__":
    mcp.run()
```

Try it from the shell first to see what the agent will see:

```
curl "https://wttr.in/Paris?format=3"
# Paris: ⛅️  +18°C
```

The docstring is doing real work here — FastMCP exposes it as the tool's `description`, which is what the model sees when deciding whether to call this tool. Treat docstrings as prompt engineering, not documentation.

## Part 5: More Than One Tool

A server can expose any number of tools. Each one is just another decorated function.

Let's add a second tool that hits [open-notify](http://open-notify.org), which reports who's currently aboard the International Space Station.

```python
from fastmcp import FastMCP
import httpx

mcp = FastMCP("weather-and-space")

@mcp.tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    response = httpx.get(f"https://wttr.in/{city}?format=3")
    return response.text.strip()

@mcp.tool
def who_is_in_space() -> str:
    """List the people currently aboard the ISS."""
    data = httpx.get("http://api.open-notify.org/astros.json").json()
    names = [p["name"] for p in data["people"]]
    return f"{data['number']} people in space: {', '.join(names)}"

if __name__ == "__main__":
    mcp.run()
```

That's it. Both tools are now available to any agent that connects. Notice that `who_is_in_space` takes no arguments — FastMCP handles the empty-parameter case the same way as everything else.

## Part 6: Connecting an Agent

This part is brief — building agents is covered in the [agents course](../agents/agents.md). But it's worth seeing how the server we just built actually gets used.

The cleanest way to try the server out is through an MCP-aware client. Claude Desktop, Cursor, and many others can be pointed at a stdio MCP server by adding it to their config file. For Claude Desktop the entry looks like this:

```json
{
  "mcpServers": {
    "weather-and-space": {
      "command": "python",
      "args": ["/absolute/path/to/weather_mcp.py"]
    }
  }
}
```

Restart the client and the two tools appear. Ask it "what's the weather in Paris and who's in space?" and watch it call both.

For a programmatic agent like the loop we built in the previous course, you'd connect using FastMCP's client:

```python
from fastmcp import Client

async with Client("weather_mcp.py") as client:
    tools = await client.list_tools()
    result = await client.call_tool("get_weather", {"city": "Paris"})
    print(result)
```

From here, wiring this into an OpenAI tool-calling loop is mechanical: the schemas from `list_tools()` become the `tools=` argument, and when the model emits a tool call you forward it to `client.call_tool()`. The shape of the agent loop is unchanged.

## Recap

You've now built three things:

1. **A function** — callable only from inside one Python process.
2. **An HTTP API** — callable over the network, but with no standard way for agents to discover it.
3. **An MCP server** — callable over a standard protocol, self-describing, ready for any MCP-compatible agent.

The progression is the lesson. Each step adds one layer (network access, then agent-discoverable schemas) without changing the underlying function. The function is the work. Everything else is plumbing.

That's enough to expose useful tools to real agents. The next steps, once you want to go further:

- **HTTP transport.** `mcp.run(transport="http", port=8000)` runs over Streamable HTTP instead of stdio. Use this for remote servers; stdio is for local ones launched as subprocesses.
- **Authentication.** Stdio servers inherit the parent process's credentials. HTTP servers need real auth — FastMCP supports OAuth and bearer tokens.
- **Real error handling.** When `httpx.get` fails the model sees a Python traceback as the tool result, which it can often recover from but isn't ideal. Wrap calls in try/except and return a clear error string.
- **Tool descriptions.** Once you have more than a handful of tools, the docstrings start to matter a lot. Write them like prompts: state what the tool does, what arguments mean, and what the return value looks like.

## But what about resources and prompts?

If you've been reading about MCP, you've probably seen *resources* and *prompts* mentioned alongside *tools*. Here's how they fit.

MCP servers can expose three kinds of thing:

- **Tools** — functions the agent can *call* to take an action or fetch information. This is what we built.
- **Resources** — read-only data the agent (or the user) can *pull*, addressed by URI. Think files, database rows, API responses that don't take parameters. The agent decides whether to read them; they're not invoked like functions.
- **Prompts** — reusable prompt templates the user (not the agent) can invoke from the client UI, often as slash commands.

Tools are the most common and the most useful, which is why we focused on them. Resources matter when you want the agent to *browse* a corpus rather than query it function-style. Prompts matter when you're building user-facing workflows in a client like Claude Desktop. All three use the same FastMCP decorator pattern — `@mcp.resource(...)` and `@mcp.prompt` — and live in the same server.

## Further reading

- **[modelcontextprotocol.io](https://modelcontextprotocol.io)** — the official MCP specification, with deeper detail on transports, resources, prompts, and sampling.
- **[gofastmcp.com](https://gofastmcp.com)** — FastMCP's documentation, with guides for client building, HTTP transport, and OAuth.
- **[Anthropic's MCP announcement](https://www.anthropic.com/news/model-context-protocol)** — the original write-up on why MCP exists and the problem it's trying to solve.
- **[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)** — a reference collection of MCP servers (filesystem, git, GitHub, Slack, Postgres, and more). Read a couple to see how non-trivial servers are structured.

Once a tool is wrapped in MCP, it stops being yours — it becomes a building block any agent ecosystem can pick up.

**Next:** [From a System Prompt to a Skill](../skills/skills.md) — tools give an agent abilities; next we give it the know-how to use them well.
