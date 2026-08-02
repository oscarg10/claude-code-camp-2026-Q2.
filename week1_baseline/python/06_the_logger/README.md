# 06 · The Logger (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/06_the_logger/requirements.txt
```

The launcher at `week1_baseline/bin/python/06_the_logger` assumes `.venv`
already exists at the repo root and has these dependencies installed.

---

`boukensha.Logger` records each agent run as structured JSON Lines. It is a
file logger, not user-facing display output — the console `print` lines
that showed `[iteration N/M]` and `tool call → ...` in `05_agent_loop` are
gone; that detail now goes to the session log file instead.

## Session Logs

Each `Logger` instance creates a session id and writes one log file for
that session:

```text
.boukensha/sessions/<session-id>.jsonl
```

Every line is a complete JSON object with `session_id`, `at`, and `phase`
fields, plus phase-specific data. This keeps logs grep/tail friendly and
machine readable.

```json
{"phase":"session_start","session_id":"20260802T183512Z-bc33a33f","at":"2026-08-02T14:35:12-04:00"}
{"phase":"iteration","n":1,"max":25,"session_id":"20260802T183512Z-bc33a33f","at":"2026-08-02T14:35:12-04:00"}
```

Model response lines include the active task, provider, model, normalized
token counts, and estimated USD cost when the backend has token pricing
data:

```json
{"phase":"response","task":"player","provider":"anthropic","model":"claude-haiku-4-5","input_tokens":707,"output_tokens":56,"cost_usd":0.000987}
```

## New Files

| File | Description |
|---|---|
| `boukensha/logger.py` | `Logger` — writes one JSONL line per phase of an agent run |

## Updated Files

| File | Change |
|---|---|
| `boukensha/agent.py` | Gains a `logger=` param (default: a fresh `Logger()`); every console `print` is replaced by a `self.logger.*` call; tool dispatch is now wrapped in `try/except Exception` so a failing tool call is logged and fed back to the model as an error result instead of crashing the loop |
| `boukensha/config.py` | Drops the unused `mud_host`/`mud_port`/`mud_username`/`mud_password` properties |
| `boukensha/__init__.py` | Exports `Logger`; adds module-level state functions `config()`, `debug()`/`is_debug()`, `quiet()`/`loud()`/`is_quiet()` |

`boukensha/context.py`, `boukensha/prompt_builder.py`, `boukensha/client.py`,
`boukensha/errors.py`, `boukensha/registry.py`, `boukensha/tool.py`,
`boukensha/message.py`, `boukensha/backends/*.py`, and
`boukensha/tasks/*.py` carry forward unchanged from `05_agent_loop`.

## `boukensha.Logger`

A plain object with one method per phase:

| Method | Phase | Logs |
|---|---|---|
| `iteration(n, max)` | `iteration` | loop counter |
| `limit_reached(kind, n, max)` | `limit_reached` | the iteration ceiling was hit |
| `prompt(messages, tools)` | `prompt` | message count/roles, tool names |
| `tool_call(name, args)` | `tool_call` | tool name and arguments |
| `tool_result(name, result, ok=True, error=None)` | `tool_result` | tool result, or the caught error |
| `response(text, usage=None, stop_reason=None, task=None, backend=None)` | `response` | response text, normalized token usage, task/provider/model, estimated cost |
| `turn_end(reason, iterations, tokens=None)` | `turn_end` | how the turn ended |
| `raw(data)` | `raw` | raw provider response, only when debug mode is on |
| `close()` | — | closes the underlying file handle |

Default usage — `Agent` builds its own `Logger()` if none is passed:

```python
from boukensha import Agent, Logger

logger = Logger()
agent = Agent(context=ctx, registry=registry, builder=builder, client=client, logger=logger)
```

You can also provide a session id or override the destination directory:

```python
Logger(session_id="manual-session")
Logger(dir="/tmp/boukensha-sessions")
```

For compatibility, `log=` still accepts an explicit file path, but normal
usage should write under `.boukensha/sessions`.

## Debug Events

Call `boukensha.debug()` before running the agent to include raw provider
responses in the log:

```python
import boukensha
boukensha.debug()
```

## Tool Errors No Longer Crash the Loop

In `05_agent_loop`, a tool that raised (e.g. `registry.dispatch` hitting an
`UnknownToolError`) propagated straight out of `Agent.run()`. Starting this
step, `_handle_tool_calls` catches it:

```python
try:
    result = self.registry.dispatch(name, args)
    self.logger.tool_result(name=name, result=result, ok=True)
except Exception as e:
    result = f"ERROR: {type(e).__name__}: {e}"
    self.logger.tool_result(name=name, result=result, ok=False, error=str(e))
```

The error string becomes the tool's result — fed back to the model like any
other tool output — and the log line records `ok: false` plus the error
message, so a bad tool call shows up in the session log instead of killing
the run.

## Task Configuration

Step 6 uses the same task-based settings shape as `05`:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25
    max_output_tokens: 1024
```

When `prompt_override.system` is true, Boukensha reads
`.boukensha/prompts/player/system.md`. Otherwise it falls back to this
step's shipped `prompts/system.md`.

| Provider | Backend | Requires |
|---|---|---|
| `anthropic` | `boukensha.Anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `boukensha.OpenAI` | `OPENAI_API_KEY` |
| `gemini` | `boukensha.Gemini` | `GEMINI_API_KEY` |
| `ollama` | `boukensha.Ollama` | a local Ollama server (`host=` defaults to `http://localhost:11434`) |
| `ollama_cloud` | `boukensha.OllamaCloud` | `OLLAMA_API_KEY` |

## What It Looks Like

Running the example produces console output like this (captured from a
real run) — notably shorter than `05`'s, since the per-iteration detail now
goes to the session log instead:

```
=== BOUKENSHA Step 6: The Logger ===

Config: #<Boukensha::Config dir=/Users/.../​.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024


=== FINAL RESPONSE ===
## Summary: BOUKENSHA MUD Player Assistant Framework

**BOUKENSHA** is a Python-based AI agent framework that enables autonomous
interaction with MUD (Multi-User Dungeon) worlds...
```

The corresponding `.boukensha/sessions/<session-id>.jsonl` from that same
run has one line per phase — `session_start`, `iteration`, `prompt`,
`response` (a tool-use turn, text summarized as `"(tool use — 1 call)"`),
`tool_call`, `tool_result`, `iteration`, `prompt`, `response` (the final
`end_turn`, with usage/cost), `turn_end`.

The exact response text, iteration count, and costs depend on the model and
this file's own contents, since the agent is genuinely reading this README
to summarize it.

## Considerations

**The assistant message must be stored before the tool result.** The
Anthropic API requires the assistant's tool_use block to appear in the
message history before its corresponding tool_result. BOUKENSHA handles
this in `_handle_tool_calls` — get the order wrong and the API rejects the
request.

**The model can call multiple tools in one turn.** The loop handles this by
iterating over all tool_use blocks in a single response before making the
next API call.

**`max_iterations` is a turn ceiling.** A poorly prompted agent can loop
forever if the model keeps calling tools. BOUKENSHA stops starting new work
after 25 iterations by default and makes one short wrap-up call with tools
disabled (`tools=[]`, not omitted). This keeps the turn bounded while still
returning a useful final response.

**The agent has no way to stop itself.** The model signals it is done via
`stop_reason: "end_turn"`. BOUKENSHA watches for that signal and exits the
loop. The agent never decides unilaterally to stop.

**The logger is a file logger, not a display.** If you want to watch a run
live, `tail -f` the session file, or point `week1_baseline/ruby/log_viz`
(a small Sinatra viewer for `.boukensha/sessions/*.jsonl`) at it.

## Run Example

```sh
./week1_baseline/bin/python/06_the_logger
```
