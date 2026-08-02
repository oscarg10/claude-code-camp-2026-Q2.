# 05 · The Agent Loop (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/05_agent_loop/requirements.txt
```

The launcher at `week1_baseline/bin/python/05_agent_loop` assumes `.venv`
already exists at the repo root and has these dependencies installed.

---

The Agent Loop is the heart of BOUKENSHA. Everything built before this —
the structs, the registry, the prompt builder, the client — was setup. The
loop is where the agent actually does work.

## New Files

| File | Description |
|---|---|
| `boukensha/agent.py` | The agent loop — sends requests, dispatches tools, and knows when to stop |

## Updated Files

| File | Change |
|---|---|
| `boukensha/client.py` | `call()` now accepts a `tools=` override, threaded through to the payload |
| `boukensha/prompt_builder.py` | `to_api_payload()` threads `tools=` through; adds `parse_response()`, delegating to the backend |
| `boukensha/backends/*.py` | `to_payload()` gains a `tools=` override; each backend adds `parse_response()` normalizing its raw response, plus `_assistant_message`/`_assistant_parts` for replaying tool-using assistant turns |
| `boukensha/tasks/base.py` | Adds `max_iterations(settings)` / `max_output_tokens(settings)`, with `DEFAULT_MAX_ITERATIONS = 25` / `DEFAULT_MAX_OUTPUT_TOKENS = 1024` fallbacks |

`boukensha/config.py`, `boukensha/context.py`, `boukensha/backends/base.py`,
and `boukensha/tasks/player.py` carry forward unchanged from
`04_api_client` — `Context` has carried its `task` field since `03`.

## How It Works

```
send messages to API
        ↓
stop_reason == "tool_use"?
    yes → extract tool calls
        → dispatch each tool via Registry
        → inject results as tool_result messages
        → go back to top
    no  → return final text response
```

## `boukensha.Agent`

| Method | Description |
|---|---|
| `run()` | Starts the loop and returns the final text response when the agent is done |

## Every Backend Speaks the Same Normalized Shape

Five providers means five different response formats — Anthropic nests
tool calls inside `content`, Ollama puts them in `message["tool_calls"]`,
OpenAI nests them under `choices[0]["message"]["tool_calls"]`, and Gemini
calls them `functionCall` parts. Rather than teach the Agent loop about
each of these, every backend implements `parse_response`, converting its
raw response into one common shape:

```python
{
    "stop_reason": "tool_use" | "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
    ],
}
```

`Agent` only ever sees this shape — it calls `self.builder.parse_response(response)`,
which delegates to the backend, and never inspects a raw provider response.

The conversion also runs in reverse. When the conversation history is
replayed on the next request, Ollama, Ollama Cloud, OpenAI, and Gemini each
rebuild a provider-specific assistant message from the normalized `content`
blocks via a private `_assistant_message` (or `_assistant_parts`) method —
the inverse of `parse_response`. Anthropic's `content` array doubles as
both the normalized shape and the wire format, so it needs no extra
conversion.

**Tool call IDs aren't universal.** Anthropic and OpenAI assign every tool
call a unique `id`, echoed back in the `tool_result`. Ollama, Ollama Cloud,
and Gemini don't assign call ids at all — those backends reuse the tool's
`name` as its `id` and match the `tool_result` back to the call by name.
This is a real difference between the providers' APIs, not a porting
artifact.

## Task Configuration

This step uses the task-based configuration introduced in the earlier
baseline steps:

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
step's shipped `prompts/system.md`. `max_iterations` controls model
round-trips per turn before wind-down, and `max_output_tokens` is passed to
each model reply.

Every backend still takes a `model=` argument; `examples/example.py` gets
both provider and model from `tasks.player`, then builds the matching
backend. The backend validates the model at construction time and exposes
metadata such as `context_window`, `usage_unit`, and token cost estimates.

| Provider | Backend | Requires |
|---|---|---|
| `anthropic` | `boukensha.Anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `boukensha.OpenAI` | `OPENAI_API_KEY` |
| `gemini` | `boukensha.Gemini` | `GEMINI_API_KEY` |
| `ollama` | `boukensha.Ollama` | a local Ollama server (`host=` defaults to `http://localhost:11434`) |
| `ollama_cloud` | `boukensha.OllamaCloud` | `OLLAMA_API_KEY` |

```python
# Anthropic
backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model="claude-sonnet-4-6")

# Ollama running locally
backend = Ollama(model="gemma4")

# Ollama Cloud
backend = OllamaCloud(api_key=os.environ["OLLAMA_API_KEY"], model="kimi-k2.5:cloud")
```

## What the Loop Looks Like

Running the example produces output like this (captured from a real run):

```
=== BOUKENSHA Step 5: Agent Loop ===

Config: #<Boukensha::Config dir=.../.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024

[iteration 1/25]
  tool call → read_file({'path': 'README.md'})
  tool result → # 05 · The Agent Loop (Python)

## Setup

This step (an

=== FINAL RESPONSE ===
This MUD player assistant framework, called BOUKENSHA, is a Python-based
system that helps players interact with a MUD (Multi-User Dungeon) world...
```

The exact response text and iteration count depend on the model and this
file's own contents, since the agent is genuinely reading this README to
summarize it.

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
disabled (`tools=[]`, not omitted — an important distinction, since
omitting `tools` entirely means "derive from the registered tools as
usual"). This keeps the turn bounded while still returning a useful final
response.

**The agent has no way to stop itself.** The model signals it is done via
`stop_reason: "end_turn"`. BOUKENSHA watches for that signal and exits the
loop. The agent never decides unilaterally to stop.

## Run Example

```sh
./week1_baseline/bin/python/05_agent_loop
```
