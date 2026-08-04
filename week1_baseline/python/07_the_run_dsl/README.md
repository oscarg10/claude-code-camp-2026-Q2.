# 07 · The `boukensha.run` DSL (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/07_the_run_dsl/requirements.txt
```

The launcher at `week1_baseline/bin/python/07_the_run_dsl` assumes `.venv`
already exists at the repo root and has these dependencies installed.

---

Every previous step required manually creating and wiring together a
`Context`, `Registry`, a `Backend`, a `PromptBuilder`, a `Client`, a
`Logger`, and an `Agent`. This step hides all of that behind one function
call and a tool-registration callback: `boukensha.run()`.

## New Files

| File | Description |
|---|---|
| `boukensha/run_dsl.py` | `RunDSL` — the tiny object passed into the registration callback, exposing only `tool()` |

## Updated Files

| File | Change |
|---|---|
| `boukensha/__init__.py` | Adds `run()`, the top-level entry point |
| `boukensha/logger.py` | Adds `turn(n)` and `subscribe(block)` — both currently unused by this step, see below |
| `boukensha/config.py` | Re-adds the `mud_host`/`mud_port`/`mud_username`/`mud_password` properties that `06` had dropped |
| `boukensha/errors.py` | Re-adds `LoopError` — still declared but never raised anywhere |

`boukensha/agent.py`, `boukensha/context.py`, `boukensha/prompt_builder.py`,
`boukensha/client.py`, `boukensha/registry.py`, `boukensha/tool.py`,
`boukensha/message.py`, `boukensha/backends/*.py`, and
`boukensha/tasks/*.py` carry forward unchanged from `06_the_logger`.

## `boukensha.run()`

```python
def run(task, system=None, model=None, backend=None, api_key=None,
        ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    ...
```

| Argument | Default | Description |
|---|---|---|
| `task` | *(required)* | The user message handed to the agent |
| `system` | the player task's system prompt | System prompt override |
| `model` | the player task's configured model | Model name override |
| `backend` | the player task's configured provider | `"anthropic"`, `"openai"`, `"gemini"`, `"ollama"`, or `"ollama_cloud"` |
| `api_key` | the matching `*_API_KEY` env var | Not needed for `"ollama"` |
| `ollama_host` | `"http://localhost:11434"` | Ollama base URL |
| `log` | `None` | Optional JSONL path override — by default, logs go to `.boukensha/sessions/<session-id>.jsonl` |
| `max_output_tokens` | the player task's configured value (1024) | Max tokens per API response |
| `block` | `None` | Callable invoked as `block(dsl)` to register tools before the run starts |

`run()` loads config, resolves every unset argument from `tasks.player` in
`settings.yaml`, builds the matching backend, calls `block(dsl)` if given,
constructs everything else internally, sends `task` as the first user
message, runs the agent to completion, and closes the logger — even if the
run raises.

## `boukensha.RunDSL`

A tiny host object passed into `block`, exposing only `tool()`:

```python
def register(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda path: Path(path).read_text(),
    )

result = boukensha.run(task="Summarise lib/boukensha.py", block=register)
```

Python has no equivalent of Ruby's `instance_eval` (which lets the block's
`self` become the DSL object, so a Ruby caller can write a bare `tool
"name", ...` with no receiver). The Python port makes the receiver
explicit instead — `block` is a plain function that takes `dsl` as its one
argument, and calls `dsl.tool(...)` on it.

## Before and After

**`06` — manual plumbing:**

```python
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings, user_prompts_dir=config.user_prompts_dir, default_prompts_dir=Config.PROMPTS_DIR,
)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)
backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model=Player.model(player_settings))
builder = PromptBuilder(ctx, backend)
client = Client(builder)
logger = Logger()
agent = Agent(context=ctx, registry=registry, builder=builder, client=client, logger=logger,
              task_settings=player_settings)

registry.tool("read_file", description="Read a file",
              parameters={"path": {"type": "string"}},
              block=lambda path: Path(path).read_text())

ctx.add_message("user", "Read lib/boukensha.py")
agent.run()
```

**`07` — just describe what you want:**

```python
def register(dsl):
    dsl.tool("read_file", description="Read a file",
             parameters={"path": {"type": "string"}},
             block=lambda path: Path(path).read_text())

boukensha.run(task="Read lib/boukensha.py", block=register)
```

## `Logger.turn()` and `Logger.subscribe()` Are New but Unused Here

This step's `Logger` gains a `turn(n)` phase-logging method and a
`subscribe(block)` hook that gets called with every event as it's written
— but nothing in `run()`, `RunDSL`, or `examples/example.py` calls either
one yet. They read like groundwork for a future step (a per-turn phase
distinct from per-iteration, and a pub/sub mechanism for something like a
live-updating display tailing a running session). Ported and exercised in
isolation (not by the example) to confirm they behave correctly:

```python
logger = Logger()
logger.subscribe(lambda event: print("saw:", event))
logger.iteration(n=1, max=25)
# saw: {'phase': 'iteration', 'n': 1, 'max': 25}
```

Subscribers receive the phase event *without* `session_id`/`at` — those two
fields are only added to the copy that gets written to the JSONL file, not
to the dict handed to subscribers.

## Task Configuration

Unchanged from `06` — `run()` introduces no new `settings.yaml` keys:

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

| Provider | Backend | Requires |
|---|---|---|
| `anthropic` | `boukensha.Anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `boukensha.OpenAI` | `OPENAI_API_KEY` |
| `gemini` | `boukensha.Gemini` | `GEMINI_API_KEY` |
| `ollama` | `boukensha.Ollama` | a local Ollama server (`ollama_host=` defaults to `http://localhost:11434`) |
| `ollama_cloud` | `boukensha.OllamaCloud` | `OLLAMA_API_KEY` |

## What It Looks Like

Running the example produces console output like this (captured from a
real run):

```
=== BOUKENSHA Step 7: The Boukensha.run DSL ===

Config: #<Boukensha::Config dir=/Users/.../.boukensha tasks=player>


=== FINAL RESPONSE ===
## Summary: BOUKENSHA MUD Player Assistant Framework

**BOUKENSHA** is a Python-based AI agent framework designed to autonomously
interact with MUD (Multi-User Dungeon) worlds...
```

The `session_start` line in that run's `.boukensha/sessions/<id>.jsonl` now
carries `run()`'s resolved settings as its snapshot:

```json
{"phase":"session_start","task":"player","max_iterations":25,"max_output_tokens":1024,"model":"claude-haiku-4-5","provider":"anthropic"}
```

The exact response text, iteration count, and costs depend on the model and
this file's own contents, since the agent is genuinely reading this README
to summarize it.

## Considerations

**The assistant message must be stored before the tool result.** The
Anthropic API requires the assistant's tool_use block to appear in the
message history before its corresponding tool_result. `Agent` handles this
in `_handle_tool_calls` — unchanged since `05`.

**The model can call multiple tools in one turn.** The loop iterates over
every tool_use block in a single response before making the next API call.

**`max_iterations` is a turn ceiling, not a hard cap.** `Agent` stops
starting new work after the limit and makes one short wrap-up call with
tools disabled instead of raising.

**The agent has no way to stop itself.** It watches for
`stop_reason: "end_turn"` from the model and exits the loop then — it never
decides unilaterally to stop.

**`run()` always closes its logger, even on failure.** An invalid `backend`
or a network error still runs the `finally` clause and closes the session
file cleanly.

## Run Example

```sh
./week1_baseline/bin/python/07_the_run_dsl
```
