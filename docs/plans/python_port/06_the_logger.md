# Python Port Plan — 06 · The Logger

## Goal

Port `week1_baseline/ruby/06_the_logger` to Python, creating
`week1_baseline/python/06_the_logger` from `05_agent_loop`'s already-correct
Python port plus this step's additions. This step adds `Boukensha::Logger` —
a structured JSON-Lines file logger that records every phase of an agent
run (`session_start`, `iteration`, `prompt`, `tool_call`, `tool_result`,
`response`, `limit_reached`, `turn_end`, and — only in debug mode — `raw`)
to `.boukensha/sessions/<session-id>.jsonl`. `Agent` is wired to a `Logger`
instance and calls it at every one of those points instead of printing to
the console. Tool dispatch also gains error handling: a failing tool call no
longer crashes the loop — it's caught, logged with `ok: false`, and fed back
to the model as an error string result.

## Starting state (found during planning)

`week1_baseline/python/06_the_logger/` doesn't exist yet — same situation
`05_agent_loop` was in relative to `04`. This plan builds the step directly
from `05_agent_loop`'s already-correct Python port. `week1_baseline/bin/python/06_the_logger`
already exists (untracked) and matches the established launcher pattern
exactly — nothing to fix there. `week1_baseline/bin/ruby/06_the_logger`
also already exists and works.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/06_the_logger/README.md` | Spec/behaviour doc — session log format, `Logger` method table, debug-mode note, task config table, are ported from here |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/logger.rb` | `Boukensha::Logger` — the whole new step: session id/path resolution, one write method per phase, `execution_metadata` (task/provider/model/usage/cost normalization) |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/agent.rb` | `Agent` gains a `logger:` param (default `Logger.new`); every former `puts` call is replaced by a `@logger.*` call; `handle_tool_calls` gains a `rescue StandardError` around `registry.dispatch` |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/config.rb` | Drops the four `mud_*` accessors (`mud_host`/`mud_port`/`mud_username`/`mud_password`) — dead code cleanup, unrelated to logging |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/errors.rb` | Drops `LoopError` (was already dead code as of `05`) |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/context.rb` | Cosmetic-only whitespace realignment — no behavior change |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/prompt_builder.rb` | Adds `attr_reader :backend` — Ruby-only concern, see Design Considerations |
| `week1_baseline/ruby/06_the_logger/lib/boukensha.rb` | Adds module-level state: `Boukensha.config`, `.quiet!`/`.loud!`/`.quiet?`, `.debug!`/`.debug?`; requires `logger` and (newly, explicitly) `backends/base` |
| `week1_baseline/ruby/06_the_logger/examples/example.rb` | Builds a `Logger.new`, passes `logger:` into `Agent.new`, banner text updated to "Step 6: The Logger". Port line-for-line. |
| `week1_baseline/ruby/06_the_logger/lib/boukensha/tool.rb`, `message.rb`, `registry.rb`, `client.rb`, `backends/*.rb`, `tasks/base.rb`, `tasks/player.rb` | Unchanged from `05_agent_loop` (diffed — byte-identical) |
| `week1_baseline/ruby/06_the_logger/Gemfile` / `Gemfile.lock` | Still just `dotenv` — `Logger` uses only Ruby stdlib (`json`, `fileutils`, `securerandom`, `time`) |

Also reference the already-completed `05_agent_loop` port
(`week1_baseline/python/05_agent_loop/`) — this step's Python source
directory is built starting from a copy of that one's `boukensha/`,
`prompts/`, and `requirements.txt`.

## Design Considerations

- **Whole new step directory, seeded from `05`, not a stale-copy fix** —
  same situation as `05` was relative to `04`.
- **The console output that existed since `01` is gone.** Every `puts` in
  `Agent` (`"[iteration N/M]"`, `"  tool call → ..."`, `"  tool result →
  ..."`) is replaced by a `Logger` call. Running the example now prints only
  the surrounding banner/config lines from `example.py` — the actual
  iteration-by-iteration detail goes to the `.jsonl` session log instead.
  This is a real, user-visible behavior change carried faithfully from the
  Ruby source, not a bug — matches the Ruby README's own framing: *"It is a
  file logger, not user-facing display output."*
- **Tool dispatch failures no longer crash the loop.** In `05`,
  `registry.dispatch` raising `UnknownToolError` (or anything else)
  propagated straight out of `Agent.run`. In `06`, `_handle_tool_calls`
  wraps the dispatch in `try/except Exception` (Ruby: `rescue StandardError`),
  turns the failure into `f"ERROR: {type(e).__name__}: {e}"` as the tool
  result text fed back to the model, and logs `tool_result(..., ok=False,
  error=str(e))`. This is a genuine behavior change, not a porting
  side-effect — flagged here so it doesn't read as scope creep when
  reviewed.
- **`Agent(logger=...)` needs a `None`-sentinel default, not Ruby's
  `logger: Logger.new`.** Ruby re-evaluates keyword-argument defaults on
  every call, so `logger: Logger.new` transparently creates a fresh
  `Logger` (and thus a fresh session file) for every `Agent.new` that omits
  it. Python evaluates a default expression **once**, at function-definition
  time — `def __init__(self, ..., logger=Logger()):` would silently share
  one `Logger` (and one open session file) across every `Agent` instance
  that doesn't pass one explicitly. The port uses `logger=None` then
  `self.logger = logger if logger is not None else Logger()` inside the
  body, the same `None`-sentinel discipline already established for
  `tools=None` in `05`, applied here for a different, Python-specific
  reason (mutable-default-argument pitfall, not a passthrough-vs-omitted
  distinction).
- **`Boukensha.config`/`Boukensha.debug?` need a home in Python, and
  `boukensha/__init__.py` is it.** Ruby's `lib/boukensha.rb` reopens the
  `Boukensha` module itself to hold `@quiet`/`@debug`/`@config` state and
  `self.config`/`self.debug?`/etc. accessor methods — the same file that's
  the top-level namespace for every class in the library. The direct Python
  analogue of "the top-level namespace module" is `boukensha/__init__.py`,
  so the state and its accessor functions live there, following the same
  drop-the-`?`/drop-the-`!` naming convention established for
  `prompt_override?` → `is_prompt_override` in `00`:
  - `Boukensha.config` → `boukensha.config()`
  - `Boukensha.quiet!` → `boukensha.quiet()`
  - `Boukensha.loud!` → `boukensha.loud()`
  - `Boukensha.quiet?` → `boukensha.is_quiet()`
  - `Boukensha.debug!` → `boukensha.debug()`
  - `Boukensha.debug?` → `boukensha.is_debug()`
  - `quiet()`/`loud()`/`is_quiet()` are carried over as dead code, matching
    them exactly — nothing in the Ruby reference calls `Boukensha.quiet!`,
    `.loud!`, or `.quiet?` anywhere either (confirmed by grep), the same
    "port dead code faithfully" stance taken with `LoopError` in `05`
    (which is *why* it's fine that `06` drops `LoopError` outright while
    `quiet`/`loud` survive — the Ruby source made two different calls about
    two different pieces of unused code, and the port just follows both).
- **`logger.py` importing `boukensha.config()` is a real circular import,
  resolved the same way Ruby resolves it: lazily, at call time, not at
  load time.** `boukensha/__init__.py` does `from .logger import Logger`;
  `logger.py` needs `boukensha.config()` and `boukensha.is_debug()`. A
  top-level `import boukensha` inside `logger.py` is safe here specifically
  because Python inserts the `boukensha` module into `sys.modules` *before*
  executing `__init__.py`'s body — `import boukensha` from within
  `logger.py` just binds that (at-the-time partially-initialized) module
  object to a local name, and the actual attribute access
  (`boukensha.config()`, `boukensha.is_debug()`) only happens later, inside
  method bodies, by which point `boukensha/__init__.py` has finished
  running. This mirrors how Ruby's `Boukensha.config`/`Boukensha.debug?`
  calls inside `logger.rb` are resolved at call time regardless of
  `require` order.
- **`PromptBuilder.backend` needs no code change in Python.** Ruby adds
  `attr_reader :backend` because Ruby instance variables (`@backend`) are
  private by default and need an explicit reader to be visible outside the
  class — `Agent#log_response` reads `@builder.backend`. Python has no such
  visibility distinction; `self.backend`, already set in `PromptBuilder.__init__`
  in `05`, was already a public attribute. `agent.py`'s `self.builder.backend`
  just works, unchanged.
- **`config.py` loses its four `mud_*` properties, matching Ruby's
  cleanup exactly** — despite `05`'s plan noting `config.py` as "zero
  changes, port forward byte-identical." That guidance was scoped to the
  `04`→`05` diff; the `05`→`06` diff is different and does remove them.
  Confirmed by re-diffing `config.rb` directly rather than assuming
  `config.py` stays frozen forever.
- **`errors.py` needs zero changes.** `LoopError` was in the Ruby
  `05_agent_loop` reference (dead code, removed in `06`) but was *never
  added* to the Python `05_agent_loop` port in the first place (see that
  step's Open Question #1 — the resolution taken was apparently "don't
  port dead code that nothing uses," diverging from the recommendation).
  Since Python's `errors.py` already lacks `LoopError`, there's nothing to
  remove — it already matches `06`'s Ruby state by coincidence.
- **`context.py` needs zero changes** — the Ruby diff is pure whitespace
  realignment of `@task`/`@system`/`@messages`/`@tools` assignment, no
  behavior touched.
- **Timestamp format: match Ruby's `Time.now.iso8601` exactly, including
  its lack of sub-second precision.** Ruby's `iso8601` defaults to
  whole-second precision (`2026-08-02T11:06:37-04:00`, confirmed against a
  real captured session log in this repo). Python's
  `datetime.now().astimezone().isoformat()` includes microseconds whenever
  they're nonzero, which would produce a shape Ruby's logs never do. The
  port uses `.isoformat(timespec="seconds")` to suppress them and match
  byte-for-byte.
- **`SecureRandom.hex(4)` → `secrets.token_hex(4)`** for the session id's
  random suffix — direct stdlib equivalent, same 8 lowercase hex chars.
- **`e.class` (Ruby) → `type(e).__name__` (Python) in the tool-error
  message is an unavoidable language-repr difference**, same category as
  the dict-repr and `JSON.pretty_generate` differences already noted in
  `03`/`05`. Ruby's `e.class` on a custom error prints its fully-qualified
  name (e.g. `Boukensha::UnknownToolError`); Python's `type(e).__name__`
  prints just the short class name (`UnknownToolError`). Only affects the
  logged/returned error string's text, not the payload sent to the model
  provider.
- **`provider_name`'s CamelCase→snake_case regex ports literally.**
  Ruby's `backend.class.name.split("::").last.gsub(/([a-z\d])([A-Z])/, '\1_\2').downcase`
  becomes `re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", type(backend).__name__).lower()`
  — Python's `type(backend).__name__` already returns the short class name
  with no `Module::` qualifier, so the `.split("::").last` step has no
  Python equivalent to port (there's nothing to split). Verified this
  produces the same values Ruby does for every backend class name in this
  codebase: `Anthropic` → `anthropic`, `Gemini` → `gemini`, `Ollama` →
  `ollama`, `OllamaCloud` → `ollama_cloud`, `OpenAI` → `open_ai`.
- **`Logger`'s per-phase methods take a `max` parameter name, shadowing
  the `max()` builtin.** Matches Ruby's `iteration(n:, max:)` /
  `limit_reached(kind:, n:, max:)` keyword names exactly. The shadow is
  local to each tiny method body, which never calls the `max()` builtin —
  harmless, and consistent with this whole series keeping parameter names
  1:1 with the Ruby source wherever there's no actual conflict.

## Target file layout

```
week1_baseline/python/06_the_logger/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # new
  prompts/
    system.md                      # unchanged from 05_agent_loop
  boukensha/
    __init__.py                    # adds Logger export + config()/quiet()/loud()/is_quiet()/debug()/is_debug()
    config.py                      # updated: drops mud_* properties
    tool.py                        # unchanged from 05_agent_loop
    message.py                     # unchanged from 05_agent_loop
    context.py                     # unchanged from 05_agent_loop
    errors.py                      # unchanged from 05_agent_loop (already lacks LoopError)
    registry.py                    # unchanged from 05_agent_loop
    prompt_builder.py              # unchanged from 05_agent_loop (backend already public)
    client.py                      # unchanged from 05_agent_loop
    logger.py                      # new: Logger
    agent.py                       # updated: logger param, logger.* calls replacing puts, tool-dispatch error handling
    backends/
      __init__.py                  # unchanged (empty)
      base.py                      # unchanged from 05_agent_loop
      anthropic.py                 # unchanged from 05_agent_loop
      ollama.py                    # unchanged from 05_agent_loop
      ollama_cloud.py              # unchanged from 05_agent_loop
      openai.py                    # unchanged from 05_agent_loop
      gemini.py                    # unchanged from 05_agent_loop
    tasks/
      __init__.py                  # unchanged
      base.py                      # unchanged from 05_agent_loop
      player.py                    # unchanged from 05_agent_loop
  examples/
    example.py                     # updated: builds Logger(), passes logger= into Agent, banner text
week1_baseline/bin/python/06_the_logger   # already exists, matches established pattern — no change needed
```

## Porting notes (Ruby → Python mapping)

### `logger.py` (new) — `Logger`

```python
import json
import os
import re
import secrets
from datetime import datetime, timezone

import boukensha


class Logger:
    DEFAULT_SESSION_DIR = "sessions"

    def __init__(self, session_id=None, dir=None, log=None, snapshot=None):
        self.session_id = session_id or self._generate_session_id()
        self.path = log or os.path.join(dir or self._default_dir(), f"{self.session_id}.jsonl")

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._log_io = open(self.path, "a")
        self._write_log({"phase": "session_start", **(snapshot or {})})

    def iteration(self, n, max):
        self._write_log({"phase": "iteration", "n": n, "max": max})

    def limit_reached(self, kind, n, max):
        self._write_log({"phase": "limit_reached", "kind": kind, "n": n, "max": max})

    def turn_end(self, reason, iterations, tokens=None):
        self._write_log({"phase": "turn_end", "reason": reason, "iterations": iterations, "tokens": tokens})

    def prompt(self, messages, tools):
        self._write_log({
            "phase": "prompt",
            "message_count": len(messages),
            "messages": [self._serialize_message(m) for m in messages],
            "tool_count": len(tools),
            "tools": list(tools.keys()),
        })

    def tool_call(self, name, args):
        self._write_log({"phase": "tool_call", "name": name, "args": args})

    def tool_result(self, name, result, ok=True, error=None):
        self._write_log({"phase": "tool_result", "name": name, "result": str(result), "ok": ok, "error": error})

    def response(self, text, usage=None, stop_reason=None, task=None, backend=None):
        event = {
            "phase": "response",
            "text": str(text).strip(),
            "usage": usage,
            "stop_reason": stop_reason,
        }
        event.update(self._execution_metadata(task=task, backend=backend, usage=usage))
        self._write_log(event)

    def raw(self, data):
        if not boukensha.is_debug():
            return
        self._write_log({"phase": "raw", "data": data})

    def close(self):
        if self._log_io:
            self._log_io.close()

    def _default_dir(self):
        return os.path.join(boukensha.config().dir, self.DEFAULT_SESSION_DIR)

    def _write_log(self, event):
        event = dict(event)
        event["session_id"] = self.session_id
        event["at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self._log_io.write(json.dumps(event) + "\n")
        self._log_io.flush()

    def _generate_session_id(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{timestamp}-{secrets.token_hex(4)}"

    def _serialize_message(self, msg):
        return {"role": msg.role, "content": msg.content}

    def _execution_metadata(self, task, backend, usage):
        if not (task or backend or usage):
            return {}

        tokens = self._usage_tokens(usage)
        metadata = {
            "task": self._task_name(task),
            "provider": self._provider_name(backend),
            "model": backend.model if backend else None,
            "usage_unit": backend.usage_unit if backend and hasattr(backend, "usage_unit") else None,
            "usage_level": backend.usage_level if backend and hasattr(backend, "usage_level") else None,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "cost_usd": self._estimate_cost(backend, tokens),
        }
        return {k: v for k, v in metadata.items() if v is not None}

    def _task_name(self, task):
        if task is None:
            return None
        return task.task_name() if hasattr(task, "task_name") else str(task)

    def _provider_name(self, backend):
        if backend is None:
            return None
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", type(backend).__name__).lower()

    def _usage_tokens(self, usage):
        usage = usage or {}
        return {
            "input": self._first_integer(usage, "input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count"),
            "output": self._first_integer(usage, "output_tokens", "completion_tokens", "candidatesTokenCount", "eval_count"),
        }

    def _first_integer(self, data, *keys):
        try:
            for key in keys:
                value = data.get(key)
                if value is not None:
                    return int(value)
            return None
        except (TypeError, ValueError):
            return None

    def _estimate_cost(self, backend, tokens):
        if backend is None or not hasattr(backend, "estimate_cost"):
            return None
        if tokens["input"] is None or tokens["output"] is None:
            return None
        return backend.estimate_cost(tokens["input"], tokens["output"])
```

### `config.py` — drop `mud_*`

Delete the `mud_host`/`mud_port`/`mud_username`/`mud_password` `@property`
methods and their section comment. Everything else (`dig`, `tasks`,
`user_prompts_dir`, `_resolve_dir`, `_load_env`, `_load_settings`,
`__str__`/`__repr__`) is untouched.

### `agent.py` — `logger`, replace `puts`, tool-dispatch error handling

```python
from .errors import ApiError
from .logger import Logger


class Agent:
    MAX_ITERATIONS = 25
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = (
        "You have reached your action limit for this turn. Do not call any more tools.\n"
        "Briefly summarize what you accomplished, what is still unfinished, and the\n"
        "single next action you would take."
    )

    def __init__(self, context, registry, builder, client, logger=None,
                 task_settings=None, max_iterations=None, max_output_tokens=None):
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.logger = logger if logger is not None else Logger()
        self.max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
        self.max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
        self.iteration = 0

    def run(self):
        while True:
            if self._iteration_limit_reached():
                self.logger.limit_reached(kind="max_iterations", n=self.iteration, max=self.max_iterations)
                return self._wrap_up("max_iterations")

            self.iteration += 1
            self.logger.iteration(n=self.iteration, max=self.max_iterations)
            self.logger.prompt(messages=self.context.messages, tools=self.context.tools)

            response = self.client.call(**self._call_opts())
            self.logger.raw(data=response)
            parsed = self.builder.parse_response(response)

            if parsed["stop_reason"] == "tool_use":
                self._handle_tool_calls(parsed["content"], response)
            else:
                text = self._extract_text(parsed["content"])
                self._log_response(text=text, response=response)
                self.logger.turn_end(reason="completed", iterations=self.iteration)
                return text

    # _resolve_max_iterations / _resolve_max_output_tokens / _iteration_limit_reached /
    # _call_opts / _fallback_message / _extract_text — unchanged from 05_agent_loop.

    def _wrap_up(self, reason):
        try:
            self.context.add_message("user", self.WRAP_UP_DIRECTIVE)
            response = self.client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
            text = self._extract_text(self.builder.parse_response(response)["content"])
            if not text.strip():
                text = self._fallback_message(reason)
            self._log_response(text=text, response=response)
            self.logger.turn_end(reason=reason, iterations=self.iteration)
            return text
        except ApiError:
            msg = self._fallback_message(reason)
            self.logger.turn_end(reason=reason, iterations=self.iteration)
            return msg

    def _handle_tool_calls(self, content, response):
        tool_calls = [b for b in content if b.get("type") == "tool_use"]

        reasoning = self._extract_text(content)
        summary = reasoning if reasoning.strip() else (
            f"(tool use — {len(tool_calls)} call{'s' if len(tool_calls) != 1 else ''})"
        )
        self._log_response(text=summary, response=response)

        self.context.add_message("assistant", content)

        for block in tool_calls:
            name = block["name"]
            args = block["input"]
            use_id = block["id"]

            self.logger.tool_call(name=name, args=args)
            try:
                result = self.registry.dispatch(name, args)
                self.logger.tool_result(name=name, result=result, ok=True)
            except Exception as e:
                result = f"ERROR: {type(e).__name__}: {e}"
                self.logger.tool_result(name=name, result=result, ok=False, error=str(e))

            self.context.add_message("tool_result", str(result), tool_use_id=use_id)

    def _log_response(self, text, response):
        self.logger.response(
            text=text,
            usage=self._normalized_usage(response),
            stop_reason=response.get("stop_reason"),
            task=self.context.task,
            backend=self.builder.backend,
        )

    def _normalized_usage(self, response):
        if response.get("usage"):
            return response["usage"]
        if response.get("usageMetadata"):
            return response["usageMetadata"]

        usage = {}
        for key in ("prompt_eval_count", "eval_count"):
            if key in response:
                usage[key] = response[key]
        return usage or None
```

### `boukensha/__init__.py` — add `Logger`, module-level state

```python
from .agent import Agent
from .backends.anthropic import Anthropic
from .backends.gemini import Gemini
from .backends.ollama import Ollama
from .backends.ollama_cloud import OllamaCloud
from .backends.openai import OpenAI
from .client import Client
from .config import Config
from .context import Context
from .errors import ApiError, UnknownToolError, UnsupportedModelError
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

_state = {"quiet": False, "debug": False, "config": None}


def config():
    if _state["config"] is None:
        _state["config"] = Config()
    return _state["config"]


def quiet():
    _state["quiet"] = True


def loud():
    _state["quiet"] = False


def is_quiet():
    return _state["quiet"]


def debug():
    _state["debug"] = True


def is_debug():
    return _state["debug"]


__all__ = [
    "Agent", "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "UnknownToolError", "UnsupportedModelError",
    "Logger", "Message", "PromptBuilder", "Registry", "Player", "Tool",
    "config", "quiet", "loud", "is_quiet", "debug", "is_debug",
]
```

Note the import order: `from .logger import Logger` triggers `logger.py`'s
top-level `import boukensha`, which is safe (see Design Considerations) —
but only because `logger.py` doesn't touch `boukensha.config`/`is_debug` at
*import* time, only inside method bodies called later.

### Example (`example.rb` → `examples/example.py`)

Same shape as `05`'s example, with the addition of building a `Logger` and
threading it into `Agent`, plus the updated banner text:

```python
from boukensha import (
    Agent,
    Anthropic,
    Client,
    Config,
    Context,
    Gemini,
    Logger,
    Ollama,
    OllamaCloud,
    OpenAI,
    Player,
    PromptBuilder,
    Registry,
)

# ... same config/backend setup as 05 ...

builder = PromptBuilder(ctx, backend)
client = Client(builder)
# Writes structured JSONL events to .boukensha/sessions/<session-id>.jsonl.
# Call boukensha.debug() before running the agent to include the full raw
# API response in those lines.
logger = Logger()
agent = Agent(
    context=ctx,
    registry=registry,
    builder=builder,
    client=client,
    logger=logger,
    task_settings=player_settings,
)

# ... same tool registration as 05 ...

print("=== BOUKENSHA Step 6: The Logger ===")
# ... rest unchanged from 05 ...
```

## Cleanup

Nothing to clean up — fresh directory, no leftover `__pycache__` from a
prior stale copy. Standard `__pycache__` cleanup after the verification run
still applies (gitignored, but tidy).

## Configuration Schema

Unchanged from `05` — `Logger` introduces no new `settings.yaml` keys:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25        # optional, defaults to 25
    max_output_tokens: 1024   # optional, defaults to 1024
```

## Open Questions

1. **`quiet`/`loud`/`is_quiet` are dead code in the Ruby reference too —
   port them anyway?** Recommendation: yes, for the same reason `05` ported
   `LoopError` — faithful 1:1 with `boukensha.rb`, cheap to carry, and
   avoids a Python `__init__.py` that mysteriously has fewer state
   accessors than Ruby's `Boukensha` module. Since `05`'s actual
   implementation chose *not* to port `LoopError` despite that
   recommendation, flagging this explicitly in case the same call should be
   made here (i.e., drop `quiet`/`loud`/`is_quiet`, keep only `config`/
   `debug`/`is_debug`, which are the ones actually used).
2. **Session logs accumulate in `.boukensha/sessions/` with no rotation or
   cleanup.** Same as the Ruby reference — not a porting gap, just worth
   surfacing since every verification run of the ported example adds
   another real `.jsonl` file there.
3. **This step still makes real API calls** (inherited from `05`) — the
   example's prompt plausibly takes 2-3 round-trips at real, if trivial,
   Haiku-tier cost. Flagging again per this series' running convention.
