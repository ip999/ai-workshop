---
marp: true
theme: default
paginate: true
header: 'AI Workshop · Lesson 2'
footer: 'From a Function to an MCP Server'
---

<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# From a Function to an MCP Server

### Lesson 2 — tools you didn't write

In Lesson 1 you wrote `get_weather` yourself. Real agents use tools that live in another process, maintained by someone else. **MCP** is the standard for exposing them.

---

## The whole idea, up front

> MCP is the **connectivity** layer — *what* the agent can do.

A function → an HTTP API → an MCP server. The function never changes; each step just wraps it so something else can reach it.

**Today:**
1 a function → 2 an HTTP API → 3 an MCP server → 4 a real API → 5 many tools → 6 connect an agent

---

## Part 1 — A Function

One input, one output. Callable only from inside this Python process.

```python
def get_weather(city):
    return f"It's 18°C and cloudy in {city}."
```

No protocol, no schema. To use it from another machine — or another agent — you have to wrap it in something that speaks over a network.

---

## Part 2 — The Same Function, as an HTTP API

FastAPI turns it into a network endpoint with one decorator.

```python
# weather_api.py
@app.get("/weather")
def get_weather(city: str):
    return f"It's 18°C and cloudy in {city}."
```

Anyone with an HTTP client can call it — **but** an agent would need to be *told* the URL, the params, and the response shape. No standard way to discover it.

---

<!-- _class: lead -->

## 🧪 Your turn — `weather_api.py`

Build it, run `uvicorn`, and `curl` the endpoint.

→ exercise at the end of **Part 2** in [mcp.md](../../mcp/mcp.md)

---

## Part 3 — The Same Function, as an MCP Server

FastMCP is to MCP what FastAPI is to HTTP: a decorator that wraps your function.

```python
# weather_mcp.py
@mcp.tool
def get_weather(city: str) -> str:
    return f"It's 18°C and cloudy in {city}."
```

Now any MCP-compatible agent can connect and **ask "what tools do you have?"** — and get back names, descriptions, and JSON schemas you never wrote.

---

## The whole leap, side by side

```python
# FastAPI                       # FastMCP
@app.get("/weather")            @mcp.tool
def get_weather(city: str):     def get_weather(city: str) -> str:
    return ...                      return ...
```

The function is identical. **The decorator changed.** FastMCP made the tool *discoverable in a way agents understand*.

---

<!-- _class: lead -->

## 🧪 Your turn — `weather_mcp.py`

Run the server; the same function, now self-describing over MCP.

→ exercise at the end of **Part 3**

---

## Part 4 — Calling a Real API

Swap the hardcoded string for a real call. The **docstring becomes the tool's description** — what the model reads when deciding to call it.

```python
@mcp.tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return httpx.get(f"https://wttr.in/{city}?format=3").text.strip()
```

Treat docstrings as prompt engineering, not documentation.

---

## Part 5 — More Than One Tool

A server exposes any number of tools — each is just another decorated function.

```python
@mcp.tool
def who_is_in_space() -> str:
    """List the people currently aboard the ISS."""
    ...
```

`who_is_in_space` takes no arguments — FastMCP handles that the same as everything else.

---

<!-- _class: lead -->

## 🧪 Your turn — add a second tool

Add `who_is_in_space` so the server exposes two tools.

→ exercise at the end of **Part 5**

---

## Part 6 — Connecting an Agent

A client connects, asks for the tools, and calls them. What's on the wire:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list" }
→ { "tools": [{ "name": "get_weather",
      "description": "Get the current weather for a city.",
      "inputSchema": { "type": "object",
        "properties": { "city": { "type": "string" } } } }] }
```

That schema is the one you **hand-wrote** in Lesson 1 — except you didn't write it.

---

<!-- _class: lead -->

## 🧪 Your turn — `client.py`

Connect to your server and list its tools.

→ exercise at the end of **Part 6**

---

## Recap

You built three things:

1. **A function** — callable only in one process.
2. **An HTTP API** — callable over the network, but not discoverable.
3. **An MCP server** — callable over a standard protocol, self-describing.

The function is the work. Everything else is plumbing.

---

## But what about resources & prompts?

MCP servers expose three kinds of thing:

- **Tools** — functions the agent *calls*. (What we built.)
- **Resources** — read-only data the agent *pulls*, by URI.
- **Prompts** — reusable templates the *user* invokes in the client.

Same decorator pattern; tools are the common case.

---

## Next: durable know-how

Tools give the agent *abilities*. But it still re-derives *how* to use them every time.

That's what **Skills** fix — Lesson 3.

📖 Full walk-through: [mcp/mcp.md](../../mcp/mcp.md)
