"""A minimal interactive agent that brings the whole workshop together.

It gives a single model:
  - an interactive loop (instruction -> answer)
  - a sandboxed Linux shell, plus read_file / write_file convenience tools
  - short-term memory: the running conversation is compacted when it gets long
  - long-term memory: durable facts written to a file and reloaded next run

Think of it as the smallest honest sketch of a general-purpose terminal agent. It is
deliberately minimal: no auth, no streaming, error handling only where the loop
would otherwise crash.

Maps back to the courses in this repo:
  agents : the loop + the sandboxed bash tool         ../agents/agents.md
  memory : compaction + a memory file the agent edits  ../memory/memory.md

Run:  export OPENAI_API_KEY=...   then   python agent.py
Quit: Ctrl-D
"""
from openai import OpenAI
from pathlib import Path
import json
import shlex
import subprocess

client = OpenAI()

MODEL = "gpt-5-mini"
SANDBOX = "agent-sandbox"
WORKDIR = Path("/tmp/agent-work")          # host dir, bind-mounted at /workspace
MEMORY_FILE = Path("agent_memory.md")      # host-side, managed by us (not the sandbox)
COMPACT_AFTER = 24                         # compact the transcript past this many messages


# --- sandbox -------------------------------------------------------------------

def ensure_sandbox():
    """Start a long-running container with /workspace bind-mounted. Idempotent."""
    running = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{SANDBOX}$"],
        capture_output=True, text=True,
    ).stdout.strip()
    if running:
        return
    WORKDIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["docker", "rm", "-f", SANDBOX], capture_output=True)
    subprocess.run([
        "docker", "run", "-d", "--name", SANDBOX, "--rm",
        "-v", f"{WORKDIR}:/workspace", "-w", "/workspace",
        "python:3.12-slim", "sleep", "infinity",
    ], check=True)
    # python:3.12-slim ships without curl; install it once so the agent can fetch.
    print("starting sandbox (installing curl)...")
    subprocess.run(
        ["docker", "exec", SANDBOX, "bash", "-c",
         "apt-get update -qq && apt-get install -y -qq curl >/dev/null"],
        capture_output=True,
    )


# --- tools ---------------------------------------------------------------------

def bash(command):
    """Run a shell command in the sandbox and return combined stdout/stderr."""
    r = subprocess.run(
        ["docker", "exec", SANDBOX, "bash", "-c", command],
        capture_output=True, text=True, timeout=120,
    )
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    return (out or "(no output)")[:4000]


def read_file(path):
    r = subprocess.run(["docker", "exec", SANDBOX, "cat", path],
                       capture_output=True, text=True)
    return r.stdout[:4000] if r.returncode == 0 else f"Error: {r.stderr.strip()}"


def write_file(path, content):
    subprocess.run(
        ["docker", "exec", "-i", SANDBOX, "bash", "-c", f"cat > {shlex.quote(path)}"],
        input=content, text=True, check=True,
    )
    return f"Wrote {len(content)} bytes to {path}"


def remember(fact):
    """Append a durable fact to the host-side memory file."""
    with MEMORY_FILE.open("a") as f:
        f.write(f"- {fact}\n")
    return f"Remembered: {fact}"


TOOLS = [
    {"type": "function", "function": {
        "name": "bash",
        "description": "Run a bash command in the sandbox. Use for anything involving "
                       "files, code, or shell utilities (curl, grep, python, ...). "
                       "Working directory is /workspace.",
        "parameters": {"type": "object",
                       "properties": {"command": {"type": "string"}},
                       "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the sandbox by path, e.g. /workspace/notes.txt.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write (overwrite) a file in the sandbox with the given content.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "remember",
        "description": "Save a durable fact about the user or project for future "
                       "sessions: stable preferences, names, conventions, decisions. "
                       "Not for transient chatter.",
        "parameters": {"type": "object",
                       "properties": {"fact": {"type": "string"}},
                       "required": ["fact"]}}},
]

DISPATCH = {"bash": bash, "read_file": read_file,
            "write_file": write_file, "remember": remember}


# --- memory --------------------------------------------------------------------

def load_memory():
    return MEMORY_FILE.read_text().strip() if MEMORY_FILE.exists() else "(nothing yet)"


def system_prompt():
    return (
        "You are a concise, capable assistant with a sandboxed Linux shell.\n"
        "Use bash / read_file / write_file to do real work; /workspace is your cwd.\n"
        "When you learn something durable about the user or project, call remember.\n\n"
        f"What you already remember:\n{load_memory()}"
    )


def _line(m):
    role = m["role"] if isinstance(m, dict) else m.role
    content = (m.get("content") if isinstance(m, dict) else m.content) or ""
    return f"{role}: {content}"


def maybe_compact(messages):
    """Fold an over-long transcript into one summary, keeping it well-formed.

    Called only at turn boundaries (no tool call is pending), so dropping the raw
    turns can never orphan a tool result from the assistant message that asked
    for it — the failure mode the OpenAI API rejects.
    """
    if len(messages) <= COMPACT_AFTER:
        return messages
    transcript = "\n".join(_line(m) for m in messages[1:])
    summary = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user",
                   "content": "Summarize this assistant session, preserving facts, "
                              "file paths, decisions, and open threads:\n\n" + transcript}],
    ).choices[0].message.content
    return [messages[0],
            {"role": "system", "content": "Summary of the session so far:\n" + summary}]


# --- the loop ------------------------------------------------------------------

def run_turn(messages):
    """Run the agent loop until it produces a normal (non-tool) reply."""
    for _ in range(25):                      # iteration cap — a basic safety rail
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        ).choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print(f"\nagent> {msg.content}\n")
            return messages

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            preview = args.get("command") or args.get("path") or args.get("fact", "")
            print(f"  · {call.function.name}({preview})")
            try:
                result = DISPATCH[call.function.name](**args)
            except Exception as e:           # feed failures back; the model recovers
                result = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print("\nagent> (stopped: hit the tool-call limit)\n")
    return messages


def main():
    ensure_sandbox()
    messages = [{"role": "system", "content": system_prompt()}]
    print("agent ready — type a request, Ctrl-D to quit.\n")
    while True:
        try:
            user = input("you> ").strip()
        except EOFError:
            print("\nbye.")
            break
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        messages = run_turn(messages)
        messages = maybe_compact(messages)


if __name__ == "__main__":
    main()
