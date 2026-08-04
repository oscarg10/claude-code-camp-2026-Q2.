# Python Port Plan — 07 · The `Boukensha.run` DSL

## Goal

Port `week1_baseline/ruby/07_the_run_dsl` to Python, creating
`week1_baseline/python/07_the_run_dsl` from `06_the_logger`'s already-correct
Python port plus this step's addition. This step adds a single top-level
entry point — `Boukensha.run` — that wires together everything manually
assembled in every prior step (`Context`, `Registry`, a `Backend`,
`PromptBuilder`, `Client`, `Logger`, `Agent`) behind one function call and a
tool-registration block, plus a tiny `RunDSL` host object that exposes only
`tool` inside that block.

## Starting state (found during planning)

`week1_baseline/python/07_the_run_dsl/` doesn't exist yet — same situation
every prior step was in relative to its predecessor. This plan builds the
step directly from `06_the_logger`'s already-correct Python port.
`week1_baseline/bin/python/07_the_run_dsl` and
`week1_baseline/bin/ruby/07_the_run_dsl` both already exist and already
match the established launcher pattern — nothing to fix there.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/07_the_run_dsl/README.md` | Spec/behaviour doc — **contains stale/inaccurate documentation**, see Design Considerations; use the actual code as ground truth over this file's Options table |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/run_dsl.rb` | `Boukensha::RunDSL` — the block-eval host object, exposing only `tool` |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha.rb` | Adds `Boukensha.run` — the whole new step, plus the final `require_relative "boukensha/run_dsl"` |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/logger.rb` | Adds `turn(n:)` (unused — nothing calls it) and `subscribe(&block)` + notifies subscribers from `write_log` |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/config.rb` | **Re-adds** the four `mud_*` accessors that `06` had removed — see Design Considerations |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/errors.rb` | **Re-adds** `LoopError`, still declared but never raised anywhere — see Design Considerations |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/context.rb` | Cosmetic-only: whitespace realignment, no trailing newline — no behavior change |
| `week1_baseline/ruby/07_the_run_dsl/examples/example.rb` | Rewritten to call `Boukensha.run(task: ...) do ... end` instead of manually wiring every primitive. Port line-for-line, adapted for Python's lack of `instance_eval` (see Design Considerations) |
| `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/agent.rb`, `prompt_builder.rb`, `tool.rb`, `message.rb`, `registry.rb`, `client.rb`, `backends/*.rb`, `tasks/base.rb`, `tasks/player.rb` | Unchanged from `06_the_logger` (diffed — byte-identical) |
| `week1_baseline/ruby/07_the_run_dsl/Gemfile` / `Gemfile.lock` | Still just `dotenv` — `run_dsl.rb` adds no dependency |

Also reference the already-completed `06_the_logger` port
(`week1_baseline/python/06_the_logger/`) — this step's Python source
directory is built starting from a copy of that one's `boukensha/`,
`prompts/`, and `requirements.txt`.

## Design Considerations

- **Whole new step directory, seeded from `06`, not a stale-copy fix** —
  same situation as every prior step's "Starting state."
- **The Ruby README's own Options table doesn't match `Boukensha.run`'s
  actual signature — port the code's real behavior, not the table.**
  The table lists `token_budget:` (default `8192`) and `max_tokens:`
  (default `1024`) as options; neither exists on the real method (its
  actual keyword args are `task:`, `system:`, `model:`, `backend:`,
  `api_key:`, `ollama_host:`, `log:`, `max_output_tokens:` — no
  `token_budget` at all, and the token cap is spelled `max_output_tokens`,
  not `max_tokens`). The table also says `backend:` accepts only
  `:anthropic` or `:ollama`, but the actual `case backend` branches on all
  five providers (`:anthropic`, `:openai`, `:gemini`, `:ollama`,
  `:ollama_cloud`) exactly like every prior step's example. This is the
  same class of stale-documentation issue this whole series keeps finding
  (`02`'s mismatched sample output, `04`'s `PROMPTS_DIR` bug, `05`'s
  `LoopError` doc claim) — noted here rather than reproduced. The Python
  README documents the method's actual parameters and the actual
  five-provider support.
- **Python has no `instance_eval` — the DSL block becomes an explicit
  function taking the `RunDSL` instance as its argument.** Ruby's
  `RunDSL.new(registry).instance_eval(&block)` re-binds `self` inside the
  block so bare `tool "name", ...` calls resolve against the `RunDSL`
  instance without a receiver. Python has no mechanism to rebind a
  function's implicit receiver this way. The port's `run()` accepts a
  `block=` callable and invokes it as `block(dsl)` — the caller writes
  `dsl.tool(...)` explicitly instead of a bare `tool(...)`. This is the one
  structurally unavoidable shape change in this whole step; every other
  piece (`RunDSL.tool` itself, the backend dispatch, the settings
  resolution) ports as a direct 1:1 translation.
- **`config.py` regains its `mud_*` properties — port the Ruby reference's
  actual `07` state, don't "fix" what looks like a regression.** `06`'s
  plan removed them because `06`'s Ruby `config.rb` had removed them; `07`'s
  Ruby `config.rb` puts them back, unchanged from how they looked before
  `06`. This reads like accidental churn in the tutorial's own snapshot
  history (the same category of thing `05`'s plan flagged re: stale docs),
  but the instruction for this whole series is to port each step's actual
  reference state, not to second-guess or "correct" it — so `mud_host`/
  `mud_port`/`mud_username`/`mud_password` come back in `config.py` exactly
  as they were before `06` removed them.
- **`errors.py` regains `LoopError` — still dead code, still ported
  faithfully.** Confirmed by grep: nothing in `07`'s Ruby source (`lib/` or
  `examples/`) raises it. Matches the "port dead code faithfully" stance
  from `05` (`LoopError` there) and `06` (`quiet!`/`loud!`/`quiet?`) —
  except this time it's Python's `errors.py` gaining a class it didn't
  previously have, rather than keeping one it already had.
- **`Logger.turn(n)` and `Logger.subscribe(block)` are both new and both
  unused in this step.** Confirmed by grep: nothing in `run_dsl.rb`,
  `boukensha.rb`, or `example.rb` calls `logger.turn` or
  `logger.subscribe`. They read like forward-looking hooks (a per-turn
  phase distinct from per-iteration, and a pub/sub mechanism for a future
  live display — e.g. a TUI tailing a running session) that a later step
  will actually wire up. Ported anyway, same "faithful even when unused"
  stance as `LoopError`.
- **`subscribe`'s callback receives the *pre-merge* event dict — a subtle
  but real behavior to preserve exactly.** Ruby's `write_log`:
  ```ruby
  def write_log(event)
    @log_io.puts JSON.generate(event.merge(session_id: @session_id, at: Time.now.iso8601))
    @log_io.flush
    @subscribers&.each { |s| s.call(event) }
  end
  ```
  `Hash#merge` (no bang) returns a *new* hash — the local `event` passed to
  each subscriber is the original, phase-specific dict only (e.g.
  `{phase: "iteration", n: 1, max: 25}`), **without** `session_id`/`at`,
  even though the persisted JSONL line has both. Easy to get wrong by
  reusing the same dict for both the write and the notify. The Python port
  builds a separate `payload` dict for the merged/logged version and calls
  subscribers with the original `event` dict, unmodified:
  ```python
  def _write_log(self, event):
      payload = dict(event)
      payload["session_id"] = self.session_id
      payload["at"] = datetime.now().astimezone().isoformat(timespec="seconds")
      self._log_io.write(json.dumps(payload) + "\n")
      self._log_io.flush()
      for subscriber in self._subscribers:
          subscriber(event)
  ```
- **`self._subscribers` is eagerly initialized to `[]`, not lazily like
  Ruby's `@subscribers ||= []`.** Ruby only allocates the array the first
  time `subscribe` is called, and `@subscribers&.each` no-ops if it's still
  `nil`. Python just initializes `self._subscribers = []` in `__init__` and
  always iterates it — an empty-list iteration is already a no-op, so the
  eager form is behaviorally identical and simpler, matching how this
  series generally prefers a plain default over reproducing Ruby's
  memoization idiom where the two are equivalent.
- **`backend` is a plain string throughout, never a Ruby-style symbol.**
  Ruby's `backend ||= task_class.provider(task_settings).to_sym` converts
  the config's string provider name to a symbol so it can be compared with
  `case backend when :anthropic then ...`. Python has no symbol type;
  `Player.provider(settings)` already returns a plain string, and the port
  compares `backend` against string literals (`"anthropic"`, `"openai"`,
  ...) directly in an `if`/`elif` chain — consistent with how every
  provider dispatch in `05`'s and `06`'s `examples/example.py` already
  worked with plain strings, never symbols.
- **`run()`'s keyword defaults use `is None` checks, not `or`/truthy
  fallbacks**, mirroring Ruby's `||=` (which only overrides `nil`/`false`,
  never other falsy-looking-but-meaningful values) — same discipline
  already established for `tools=None` in `05` and `max_output_tokens` in
  `06`. Concretely: `system`, `model`, `backend`, `api_key`, and
  `max_output_tokens` are each resolved with `if x is None: x = ...`, not
  `x = x or ...`.
- **`ensure logger&.close` becomes a method-level `try/finally` with
  `logger` pre-declared as `None`.** Ruby's `ensure` wraps the entire
  method body implicitly; `logger` is `nil` if an exception occurs before
  its assignment line runs (e.g. an invalid `backend` raising before the
  `Logger.new` call), and `&.close` is then a safe no-op. The Python port
  sets `logger = None` before the `try:`, builds everything inside the
  `try` block, and the `finally` clause closes it only `if logger is not
  None`.
- **`Boukensha.run` lives in `boukensha/__init__.py`, next to `config()`/
  `debug()`, not in a separate module.** This mirrors Ruby's structure
  exactly: `lib/boukensha.rb` reopens the `Boukensha` module to add both
  the `config`/`quiet!`/`debug!` state accessors (ported to `__init__.py`
  in `06`) *and* `Boukensha.run`, in the same block, before any of the
  `require_relative` lines for the classes `run` itself references. That
  ordering works in Ruby because constant/method lookup happens at call
  time, not require time; it works in the Python port for the same reason
  it already worked for `config()`'s use of `Config` — by the time `run()`
  is actually *called*, every name it references (`Context`, `Registry`,
  `Player`, `Anthropic`, `RunDSL`, ...) is already bound at module scope,
  since all the `from .x import Y` lines sit above `run()`'s definition in
  `__init__.py`.
- **`examples/example.py` uses `import boukensha` and calls
  `boukensha.run(...)`/`boukensha.config()`, not `from boukensha import
  run, config`.** Every earlier step's example used `from boukensha import
  (Agent, Anthropic, ...)` because it needed to construct several classes
  directly. This step's whole point is collapsing that into one namespaced
  call — `import boukensha; boukensha.run(...)` mirrors the Ruby call site
  (`Boukensha.run(...)`, `Boukensha.config`) far more directly than
  importing `run`/`config` as bare names would.
- **`RunDSL.tool` needs no `parameters` default of its own.** Ruby's
  `tool(name, description:, parameters: {}, &block)` defaults `parameters`
  to `{}` before forwarding to `@registry.tool`. Python's
  `Registry.tool(self, name, description, parameters=None, block=None)`
  (already in place since `04`) already normalizes `parameters or {}`
  internally, so `RunDSL.tool` just forwards whatever it's given —
  `parameters=None` flows through to `Registry.tool` and gets normalized
  there, one layer down from where Ruby normalizes it. Same end result,
  no duplicated default.

## Target file layout

```
week1_baseline/python/07_the_run_dsl/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # new — documents run()'s actual signature, not the stale Ruby table
  prompts/
    system.md                      # unchanged from 06_the_logger
  boukensha/
    __init__.py                    # adds run(), imports RunDSL
    config.py                      # updated: re-adds mud_* properties
    tool.py                        # unchanged from 06_the_logger
    message.py                     # unchanged from 06_the_logger
    context.py                     # unchanged from 06_the_logger
    errors.py                      # updated: re-adds LoopError
    registry.py                    # unchanged from 06_the_logger
    prompt_builder.py              # unchanged from 06_the_logger
    client.py                      # unchanged from 06_the_logger
    logger.py                      # updated: adds turn(), subscribe(), subscriber notification
    agent.py                       # unchanged from 06_the_logger
    run_dsl.py                     # new: RunDSL
    backends/
      __init__.py                  # unchanged (empty)
      base.py                      # unchanged
      anthropic.py                 # unchanged
      ollama.py                    # unchanged
      ollama_cloud.py              # unchanged
      openai.py                    # unchanged
      gemini.py                    # unchanged
    tasks/
      __init__.py                  # unchanged
      base.py                      # unchanged
      player.py                    # unchanged
  examples/
    example.py                     # rewritten: calls boukensha.run(task=..., block=...) instead of manual wiring
week1_baseline/bin/python/07_the_run_dsl   # already exists, matches established pattern — no change needed
```

## Porting notes (Ruby → Python mapping)

### `run_dsl.py` (new) — `RunDSL`

```python
class RunDSL:
    """The object `block` is called with inside `run()`. Exposes only
    `tool`, keeping the DSL surface intentionally small."""

    def __init__(self, registry):
        self.registry = registry

    def tool(self, name, description, parameters=None, block=None):
        return self.registry.tool(name, description=description, parameters=parameters, block=block)
```

### `logger.py` — `turn`, `subscribe`, subscriber notification

```python
def __init__(self, session_id=None, dir=None, log=None, snapshot=None):
    self.session_id = session_id or self._generate_session_id()
    self.path = log or os.path.join(dir or self._default_dir(), f"{self.session_id}.jsonl")
    self._subscribers = []

    os.makedirs(os.path.dirname(self.path), exist_ok=True)
    self._log_io = open(self.path, "a")
    self._write_log({"phase": "session_start", **(snapshot or {})})

def turn(self, n):
    self._write_log({"phase": "turn", "n": n})

def subscribe(self, block):
    self._subscribers.append(block)

# ... iteration/limit_reached/turn_end/prompt/tool_call/tool_result/response/raw/close unchanged ...

def _write_log(self, event):
    payload = dict(event)
    payload["session_id"] = self.session_id
    payload["at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    self._log_io.write(json.dumps(payload) + "\n")
    self._log_io.flush()
    for subscriber in self._subscribers:
        subscriber(event)
```

### `config.py` — re-add `mud_*`

Re-insert the four `@property` methods removed in `06`, verbatim from `05`:

```python
@property
def mud_host(self):
    return self.dig("mud", "host") or "localhost"

@property
def mud_port(self):
    return self.dig("mud", "port") or 4000

@property
def mud_username(self):
    return self.dig("mud", "username")

@property
def mud_password(self):
    return self.dig("mud", "password")
```

### `errors.py` — re-add `LoopError`

```python
class UnknownToolError(Exception):
    pass


class ApiError(Exception):
    pass


class LoopError(Exception):
    pass


class UnsupportedModelError(Exception):
    pass
```

### `boukensha/__init__.py` — `run()`

```python
import os

from .agent import Agent
from .backends.anthropic import Anthropic
from .backends.gemini import Gemini
from .backends.ollama import Ollama
from .backends.ollama_cloud import OllamaCloud
from .backends.openai import OpenAI
from .client import Client
from .config import Config
from .context import Context
from .errors import ApiError, LoopError, UnknownToolError, UnsupportedModelError
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .run_dsl import RunDSL
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


def run(task, system=None, model=None, backend=None, api_key=None,
        ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    """The top-level entry point. Wires together every primitive so the
    caller only has to describe *what* to do, not *how* to plumb it.

        def register(dsl):
            dsl.tool("read_file",
                description="Read a file from disk",
                parameters={"path": {"type": "string", "description": "File path"}},
                block=lambda path: Path(path).read_text())

        result = boukensha.run(task="Summarise lib/boukensha.py", block=register)
    """
    logger = None
    try:
        cfg = config()  # loads .env; populates os.environ
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())

        if system is None:
            system = task_class.system_prompt(
                task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=Config.PROMPTS_DIR
            )
        if model is None:
            model = task_class.model(task_settings)
        if backend is None:
            backend = task_class.provider(task_settings)
        if api_key is None:
            if backend == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif backend == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif backend == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY")
            elif backend == "ollama_cloud":
                api_key = os.environ.get("OLLAMA_API_KEY")

        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)

        if block is not None:
            block(RunDSL(registry))

        if backend == "anthropic":
            be = Anthropic(api_key=api_key, model=model)
        elif backend == "openai":
            be = OpenAI(api_key=api_key, model=model)
        elif backend == "gemini":
            be = Gemini(api_key=api_key, model=model)
        elif backend == "ollama":
            be = Ollama(host=ollama_host, model=model)
        elif backend == "ollama_cloud":
            be = OllamaCloud(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )

        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else task_class.max_output_tokens(task_settings)
        )
        logger = Logger(log=log, snapshot={
            "task": task_class.task_name(),
            "max_iterations": effective_max_iterations,
            "max_output_tokens": effective_max_output_tokens,
            "model": model,
            "provider": backend,
        })
        agent = Agent(
            context=ctx, registry=registry, builder=builder, client=client, logger=logger,
            task_settings=task_settings, max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
        )

        ctx.add_message("user", task)
        return agent.run()
    finally:
        if logger is not None:
            logger.close()


__all__ = [
    "Agent", "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "LoopError", "UnknownToolError", "UnsupportedModelError",
    "Logger", "Message", "PromptBuilder", "Registry", "RunDSL", "Player", "Tool",
    "config", "quiet", "loud", "is_quiet", "debug", "is_debug", "run",
]
```

### Example (`example.rb` → `examples/example.py`)

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boukensha

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically.
os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

print("=== BOUKENSHA Step 7: The Boukensha.run DSL ===")
print()
print(f"Config: {boukensha.config()}")
print()

BASE_DIR = Path(__file__).resolve().parent.parent


def register(dsl):
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "The file path to read"}},
        block=lambda path: Path(BASE_DIR, path).read_text(),
    )
    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "The directory path to list"}},
        block=lambda path: ", ".join(
            entry for entry in os.listdir(Path(BASE_DIR, path)) if not entry.startswith(".")
        ),
    )


result = boukensha.run(
    task="Read the README.md file and summarise what this MUD player assistant framework can do.",
    block=register,
)

print()
print("=== FINAL RESPONSE ===")
print(result)
```

Note: unlike `05`/`06`, `Agent` is never constructed directly in the
example — `boukensha.run()` builds it internally. This is the whole point
of the step, not an omission.

### `README.md`

New file, following the Python README structure established in `00`-`06`:

- Overview paragraph — one entry point replaces manual wiring, adapted from
  the Ruby README's own framing.
- **New Files** table: `boukensha/run_dsl.py`. **Updated Files** table:
  `boukensha/__init__.py` (`run()`), `boukensha/logger.py` (`turn`,
  `subscribe`), `boukensha/config.py` (`mud_*` back), `boukensha/errors.py`
  (`LoopError` back, still unused).
- **`boukensha.run()`** section documenting the *actual* signature (see
  Design Considerations) — not the stale Ruby table's `token_budget`/
  `max_tokens`/two-backend claims.
- **Before and after** — the `05`-style manual-wiring snippet next to the
  one-call `boukensha.run(task=..., block=register)` snippet, adapted for
  Python's explicit `dsl` parameter instead of Ruby's `instance_eval`.
- **Considerations** — carry forward whichever of `06`'s still apply
  (assistant-before-tool-result ordering, multi-tool-call turns,
  `max_iterations` as a trigger threshold, the agent can't stop itself),
  since `Agent`'s behavior is completely unchanged this step.
- **Run Example** pointing at `./week1_baseline/bin/python/07_the_run_dsl`.

## Cleanup

Nothing to clean up — fresh directory, no leftover `__pycache__` from a
prior stale copy. Standard `__pycache__` cleanup after the verification run
still applies (gitignored, but tidy).

## Configuration Schema

Unchanged from `06` — `run()` introduces no new `settings.yaml` keys, it
only reads the same `tasks.player` shape:

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

1. **Naming the `block=` parameter.** Ruby's mechanism is an implicit
   `&block`, with no keyword name to preserve. `block=` was chosen to keep
   the closest naming parity with the Ruby source despite the semantic
   shift (explicit `dsl` argument vs. `instance_eval`); an alternative
   would be `register=` or `configure=`, which reads slightly more clearly
   at Python call sites given the callback now takes an explicit parameter.
   Recommendation: keep `block=` for consistency with this series' general
   preference for 1:1 naming wherever there's no real conflict — flagging
   in case `register=`/`configure=` is preferred instead.
2. **This step still makes real API calls**, inherited from `05`/`06` — the
   example's prompt plausibly takes 2-3 round-trips at real, if trivial,
   Haiku-tier cost. Flagging again per this series' running convention.
