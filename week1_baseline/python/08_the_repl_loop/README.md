# 08 · The REPL Loop (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/08_the_repl_loop/requirements.txt
```

The launcher at `week1_baseline/bin/python/08_the_repl_loop` assumes
`.venv` already exists at the repo root and has these dependencies
installed.

---

|  | `boukensha.run()` (`07`) | `boukensha.repl()` (`08`) |
|---|---|---|
| Entry point | one call, returns | stays alive, reads stdin |
| Turns | one | many |
| History | discarded | accumulates across turns |
| User interaction | none | stdin prompt |

## New Files

| File | Description |
|---|---|
| `boukensha/repl.py` | `Repl` — the interactive session loop: banner, command handling, per-turn `Agent` |
| `boukensha/version.py` | `VERSION = "0.8.0"`, shown in the REPL banner |

## Updated Files

| File | Change |
|---|---|
| `boukensha/__init__.py` | Adds `repl()`, the interactive entry point |
| `boukensha/agent.py` | Persists the final reply into context on every return path (not just tool-use turns) — needed so follow-up turns see prior replies |
| `boukensha/context.py` | Adds `clear_messages()`, used by the REPL's `/clear` command |
| `boukensha/config.py` | `_resolve_dir()` gains a middle tier: a `.boukensha/` directory in the current working directory now takes priority over `~/.boukensha` |
| `boukensha/client.py` | A 401 response now raises `"authentication failed (401) — check your API key"` instead of the generic failure message |

`boukensha/logger.py`, `boukensha/errors.py`, `boukensha/prompt_builder.py`,
`boukensha/registry.py`, `boukensha/run_dsl.py`, `boukensha/tool.py`,
`boukensha/message.py`, `boukensha/backends/*.py`, and
`boukensha/tasks/*.py` carry forward unchanged from `07_the_run_dsl`.

## `boukensha.Repl`

Wraps the same primitives as a single `boukensha.run()` call, but instead
of running once it stays alive: read a task from stdin, run the agent,
print the reply, loop back to the prompt. The `Context` is shared across
every turn, so conversation history accumulates naturally — the agent sees
the full transcript each time it's called. A fresh `Agent` is built for
every turn (so the per-turn iteration ceiling resets each time), reusing
the same `context`/`registry`/`builder`/`client`/`logger`.

Built-in commands:

| Command | Effect |
|---|---|
| `/quiet` | Sets an internal "quiet" flag and prints a confirmation. **Currently has no observable effect** — nothing in this codebase reads the flag back yet (see below) |
| `/loud` | Clears that same flag — also currently cosmetic-only |
| `/clear` | Wipes conversation history via `Context.clear_messages()`; tools stay registered |
| `/help` | Prints the command list |
| `/exit` / `/quit` | Leaves the REPL |
| Ctrl-D (EOF) | Leaves the REPL |
| Ctrl-C | Interrupted, caught by `repl()`, prints `"Interrupted."` and exits cleanly |

**`/quiet` and `/loud` don't suppress anything yet.** They toggle
`boukensha.is_quiet()`'s backing state, but nothing — not `Logger`, not
`Repl` — actually checks that state anywhere. This isn't a porting gap;
it's the current, real behavior of the reference this step ports from
(confirmed by grep: `is_quiet()` has no callers). The plumbing exists for
a future step to consume.

## `boukensha.repl()`

```python
def repl(system=None, model=None, backend=None, api_key=None,
         ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    ...
```

Same arguments as `run()` (see `07`'s README), minus `task` — the user
supplies tasks interactively instead. Resolves config the same way `run()`
does, calls `block(dsl)` to register tools if given, then hands off to
`Repl.start()`. Always closes the logger on the way out, including on
`KeyboardInterrupt`.

```python
def register(dsl):
    dsl.tool(
        "read_file",
        description="Read a file from disk",
        parameters={"path": {"type": "string", "description": "File path"}},
        block=lambda path: Path(path).read_text(),
    )

boukensha.repl(model="claude-haiku-4-5", block=register)
```

## What Changed in `Agent`

Before this step, only `_handle_tool_calls` added an `"assistant"` message
to `context` — needed so the next iteration's request includes the
tool-use turn. The final text reply was returned but never stored, which
was fine when `context` got thrown away right after a one-shot `run()`
call. A REPL reuses the same `Context` across turns, so the agent needs its
own prior replies in the transcript for follow-up questions to make sense:

```python
# 07 — final text returned but NOT stored in context
return text

# 08 — final text stored in context, then returned
self.context.add_message("assistant", text)
return text
```

All three of `Agent`'s exit paths — normal completion, `_wrap_up`'s
success branch, and `_wrap_up`'s `except ApiError` fallback — gained this
line.

## Config Resolution Now Checks the Working Directory

`Config._resolve_dir()`'s order became:

1. `BOUKENSHA_DIR` environment variable
2. `.boukensha/` in the current working directory, if it exists
3. `~/.boukensha` (default)

Tier 2 is new this step. It means running the REPL from inside a project
that has its own `.boukensha/` picks that up automatically, without
needing to export `BOUKENSHA_DIR` by hand.

## Task Configuration

Unchanged from `07` — `repl()` introduces no new `settings.yaml` keys:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25        # now a per-turn ceiling — every REPL turn gets a fresh count
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

Captured from a real run (piped input, since the REPL reads stdin):

```
Config: #<Boukensha::Config dir=/Users/.../.boukensha tasks=player>


╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v0.8.0)    ║
╚══════════════════════════════════════╝
  config:    /Users/.../.boukensha
  provider:  anthropic (claude-haiku-4-5)  ✓ API key set

  /quiet or /loud   toggle logging
  /clear           reset conversation history
  /exit or /quit    leave the REPL

boukensha> 
Here are the files and directories in the current directory:

1. **README.md** - A markdown file (likely documentation)
2. **boukensha** - A directory
3. **examples** - A directory
4. **prompts** - A directory
5. **requirements.txt** - A text file (likely Python dependencies)

Would you like me to explore any of these files or directories further?
boukensha> 
The first file in the list I just gave you was **README.md**.
boukensha> Goodbye.
```

The second answer demonstrates persistent history: the agent answers from
the accumulated transcript, not just the latest message — confirmed
against the session's `.jsonl` log, where the second turn's `prompt` event
shows `message_count: 5` (both prior turns' user/assistant/tool messages
are still present) versus the first turn's `message_count: 1`.

## Considerations

**The assistant message must be stored before the tool result.** Unchanged
since `05` — `Agent` handles this in `_handle_tool_calls`.

**The model can call multiple tools in one turn.** The loop iterates over
every tool_use block in a single response before making the next API call.

**`max_iterations` is a per-turn ceiling, not a hard cap on the whole
session.** Since a fresh `Agent` is built for every REPL turn, the
iteration count resets each time you send a new message — the limit only
bounds how many tool round-trips a *single* turn can take.

**The agent has no way to stop itself.** It watches for
`stop_reason: "end_turn"` and exits the loop then — it never decides
unilaterally to stop.

**`repl()` always closes its logger, even on Ctrl-C or a raised error.**
The `finally` clause runs regardless of how the session ends.

## Run Example

```sh
./week1_baseline/bin/python/08_the_repl_loop
```

This is interactive — it reads from stdin. Type a message and press Enter;
type `/exit` or press Ctrl-D to leave.
