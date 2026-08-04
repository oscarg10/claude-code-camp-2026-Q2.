# Python Port Plan — 08 · The REPL Loop

## Goal

Port `week1_baseline/ruby/08_the_repl_loop` to Python, creating
`week1_baseline/python/08_the_repl_loop` from `07_the_run_dsl`'s
already-correct Python port plus this step's addition. This step adds
`Boukensha.repl` — an interactive session loop that registers tools once,
then reads tasks from stdin in a loop, running the agent and printing
replies until the user exits. Unlike `boukensha.run()` (one shot, history
discarded), the REPL shares one `Context` across every turn so conversation
history accumulates — the agent sees the full transcript on each call.

## Starting state (found during planning)

`week1_baseline/python/08_the_repl_loop/` doesn't exist yet — same
situation every prior step was in relative to its predecessor. This plan
builds the step directly from `07_the_run_dsl`'s already-correct Python
port. `week1_baseline/bin/python/08_the_repl_loop` and
`week1_baseline/bin/ruby/08_the_repl_loop` both already exist. The Ruby
launcher explicitly exports `BOUKENSHA_DIR="$REPO_ROOT/.boukensha"` before
running; the Python launcher does **not** — it matches every prior Python
launcher's plain `cd` + `python examples/example.py` shape. This asymmetry
matters for how `examples/example.py` is ported — see Design
Considerations.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/08_the_repl_loop/README.md` | Spec/behaviour doc — **the `Logger#turn` section and the sample banner/transcript are fabricated/stale**, see Design Considerations; use the actual code as ground truth |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/repl.rb` | `Boukensha::Repl` — the whole new step: banner, command loop, per-turn `Agent` construction |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/version.rb` | Adds `VERSION = "0.8.0"`, shown in the REPL banner |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha.rb` | Adds `Boukensha.repl` (mirrors `Boukensha.run`'s resolution logic, minus `task:`), requires `version` and `repl` |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/agent.rb` | `Agent#run` and `Agent#wrap_up` now persist the final reply into `@context` on every exit path (previously only tool-use turns were persisted) |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/context.rb` | Adds `clear_messages!` — wipes `@messages`, keeps `@tools`/`@system` intact. Used by `/clear` |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/config.rb` | `resolve_dir` gains a middle tier: checks for `.boukensha/` in the current working directory before falling back to `~/.boukensha` |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/client.rb` | A 401 response now raises a specific `"authentication failed (401) — check your API key"` `ApiError` instead of the generic failure message |
| `week1_baseline/ruby/08_the_repl_loop/examples/example.rb` | Rewritten around `Boukensha.repl do ... end`; drops the `ENV["BOUKENSHA_DIR"] ||=` override every prior example had, and points its tools at **`07_the_run_dsl`'s** directory, not its own |
| `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/logger.rb`, `errors.rb`, `prompt_builder.rb`, `tool.rb`, `message.rb`, `registry.rb`, `run_dsl.rb`, `backends/*.rb`, `tasks/base.rb`, `tasks/player.rb` | Unchanged from `07_the_run_dsl` (diffed — byte-identical). `Logger#turn(n:)` already existed since `07` and is unchanged — it's a bare JSONL write, no console output (see Design Considerations re: the stale README) |
| `week1_baseline/ruby/08_the_repl_loop/Gemfile` / `Gemfile.lock` | Unchanged — still just `dotenv`; the REPL needs no new dependency |

Also reference the already-completed `07_the_run_dsl` port
(`week1_baseline/python/07_the_run_dsl/`) — this step's Python source
directory is built starting from a copy of that one's `boukensha/`,
`prompts/`, and `requirements.txt`.

## Design Considerations

- **Whole new step directory, seeded from `07`, not a stale-copy fix** —
  same situation as every prior step's "Starting state."
- **The Ruby README's `Logger#turn` section is fabricated — port the code,
  not the doc.** The README claims `Logger#turn` *"prints a `╔══ turn N
  ══╗` header at the start of each REPL turn."* The actual method
  (unchanged since `07`) is `def turn(n:); write_log(phase: "turn", n:
  n); end` — a bare JSONL write, no console output at all. Confirmed by
  reading `logger.rb` directly (not in this step's diff) and grepping for
  any box-drawing/header printing anywhere in the codebase — there is
  none. Same class of doc/code mismatch this whole series keeps finding
  (`02`, `04`, `05`, `07`'s stale-doc notes); the Python README documents
  what `turn()` actually does.
- **The Ruby README's sample banner and transcript are illustrative, not
  captured output — same as `05`'s plan flagged for that step's sample.**
  The README shows a banner reading `BOUKENSHA REPL — MUD assistant` with
  a different box width/content than what `Repl#banner` actually builds
  (which reads `BOUKENSHA MUD Assistant (v0.8.0)` plus `config:`/
  `provider:` lines and the real command list). The Python README's "What
  It Looks Like" section is captured from an actual run, per this series'
  established practice, not copied from the Ruby README's sample.
- **`/quiet` and `/loud` are real state toggles that currently do
  nothing.** Confirmed by grep: `Boukensha.quiet?` (the getter) is defined
  in `lib/boukensha.rb` but never *read* anywhere in this codebase — not
  in `Logger`, not in `Repl`, nowhere. So typing `/quiet` calls
  `Boukensha.quiet!`, prints `"(logging suppressed...)"`, and changes
  internal state that nothing consults — logging continues exactly as
  before. This isn't a porting gap; it's the reference's actual current
  behavior (the plumbing exists, the consumer doesn't yet). Ported
  faithfully — the Python REPL's `/quiet` is equally cosmetic-only right
  now, and the README says so rather than implying it works.
- **`LoopError` is still never raised anywhere** (confirmed by grep across
  the entire `08` Ruby source) — `Repl#run_turn`'s `rescue LoopError`
  clause is defensive code for an exception nothing throws, same "port
  dead code faithfully" stance as every prior step's `LoopError` note.
  Ported as `except LoopError` in `_run_turn` regardless.
- **`Agent` now persists its final reply on every exit path, not just
  tool-use turns.** Before this step, only `_handle_tool_calls` added an
  `"assistant"` message to context (needed so the next iteration's request
  includes the tool-use turn) — the final text reply was returned but
  never stored, which was fine for `06`/`07`'s one-shot `run()` calls
  (context gets thrown away right after). A REPL reuses the same `Context`
  across turns, so the agent needs its own prior replies in the transcript
  for follow-up questions to make sense (the README's own demo: *"what was
  the first file I asked you about?"*). All three return points in
  `agent.py` gain `self.context.add_message("assistant", text)` right
  before returning: the normal-completion branch in `run()`, the
  successful branch in `_wrap_up`, and the `except ApiError` fallback
  branch in `_wrap_up`.
- **`Repl` is constructed once; `Agent` is constructed fresh every turn.**
  `Repl.__init__` receives `context`, `registry`, `builder`, `client`,
  `logger` once and holds them for the whole session. `_run_turn` builds a
  brand-new `Agent` on every call, passing the same shared `context`/
  `registry`/`builder`/`client`/`logger` — so each turn gets its own fresh
  `iteration = 0` counter (the per-turn iteration ceiling resets every
  turn) while the conversation `Context` keeps accumulating across turns.
  This is a deliberate two-tier lifetime split, not an oversight — ported
  exactly as structured.
- **Python's `sys.stdin.readline()` replaces Ruby's `$stdin.gets` — not
  the `input()` builtin.** Both `.gets` and `.readline()` block until a
  newline and return the line *with* its trailing `\n` still attached, and
  both signal EOF (Ctrl-D) by returning an empty/falsy value (`nil` in
  Ruby, `""` in Python) rather than raising. Python's `input()` builtin is
  a worse match here: it strips the newline itself (Ruby's `.gets` doesn't
  — the code does `input.chomp.strip` explicitly) and it raises
  `EOFError` on EOF instead of returning a sentinel, which would need an
  extra `try/except` this port doesn't need with `readline()`.
- **`Repl.start`'s banner needs `print(..., end="")`, not a bare
  `print(...)`, to match Ruby's `puts` trailing-newline semantics
  exactly.** Ruby's `puts` only appends `\n` if the string doesn't already
  end with one; the banner heredoc already ends with a blank line (two
  trailing `\n`s), so `puts banner` adds nothing extra. Python's `print()`
  *always* appends its own `\n` regardless of what the string already ends
  with — printing the Python banner string (built to end the same way,
  with a trailing blank line) via plain `print()` would add a third,
  unwanted blank line. The port builds `_banner()` to return the exact
  string (leading blank line, box, config/provider lines, blank line,
  three command lines, trailing blank line) and prints it with
  `print(self._banner(), end="")`.
- **The banner's version padding ports as a direct arithmetic
  translation.** Ruby: `" " * (9 - ver.length)` right-pads the version
  string inside the fixed-width box border. Python: `" " * (9 -
  len(ver))` — identical arithmetic, same fallback (`ver = self.version or
  "?.?.?"`, 5 characters, same length as the real `"0.8.0"`).
- **`config.py`'s `_resolve_dir` gains a real, meaningful new tier — not
  just a cosmetic reformat.** The order becomes: (1) `BOUKENSHA_DIR` env
  var, (2) `.boukensha/` in the current working directory if it exists,
  (3) `~/.boukensha`. This is why Ruby's `08` launcher
  (`bin/ruby/08_the_repl_loop`) now exports `BOUKENSHA_DIR` explicitly and
  `example.rb` dropped its own override — the launcher `cd`s into
  `ruby/08_the_repl_loop` *before* running, so without an explicit
  `BOUKENSHA_DIR`, tier 2 would look for (and not find)
  `ruby/08_the_repl_loop/.boukensha`, falling through to the real
  `~/.boukensha` on tier 3.
- **Python's `examples/example.py` keeps the `BOUKENSHA_DIR` override that
  Ruby's `example.rb` dropped — a deliberate divergence, not an oversight.**
  The existing `week1_baseline/bin/python/08_the_repl_loop` launcher
  (already present, matches every other Python launcher's template) does
  **not** export `BOUKENSHA_DIR` the way the Ruby launcher now does. If
  the Python example also dropped its own override, running it via that
  launcher would fall through the new tier-2/tier-3 resolution to the
  real `~/.boukensha` — a surprising, environment-dependent default that
  every other step's verification run has deliberately avoided by pointing
  at the repo's own `.boukensha/`. The port keeps
  `os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))`
  in `example.py`, unchanged from `07`, so Python's actual runtime
  behavior matches Ruby's (both land on the repo's `.boukensha/`) even
  though the two languages now assign that responsibility to different
  files. Flagged as an Open Question in case the Python launcher should
  instead be updated to export `BOUKENSHA_DIR` the way Ruby's does, mirroring
  the reference's structural move exactly.
- **`example.py`'s tool sandbox points at `07_the_run_dsl`'s directory,
  not `08_the_repl_loop`'s own — ported exactly, not "fixed."** Ruby's
  `base_dir = File.expand_path("../../07_the_run_dsl", __dir__)` reads
  from the *previous* step's folder rather than its own — presumably so
  there's a richer, already-familiar set of files to ask multi-turn
  questions about (matching the README's demo transcript: read one file,
  then ask about "the first file I asked about"). Ported as
  `BASE_DIR = Path(__file__).resolve().parent.parent.parent / "07_the_run_dsl"`
  (`.../python/08_the_repl_loop/examples/example.py` → up three to
  `python/`, then into `07_the_run_dsl`).
- **`Boukensha.repl` duplicates `Boukensha.run`'s config/backend
  resolution block almost verbatim — the reference doesn't factor it into
  a shared helper, so the port doesn't either.** Same "thin 1:1 port, no
  abstraction the reference doesn't have" stance already applied to
  `Ollama`/`OllamaCloud`'s duplicated `parse_response` in `05`. `run()`
  and `repl()` in `boukensha/__init__.py` independently repeat the
  `cfg`/`task_class`/`task_settings`/`system`/`model`/`backend`/`api_key`
  resolution and the backend-construction `if`/`elif` chain.
- **`rescue Interrupt` → `except KeyboardInterrupt`, at the same
  `repl()`-function scope as Ruby's `Boukensha.repl` method scope, not
  inside `Repl.start`.** Ctrl-C during any part of the session — including
  mid-agent-call — propagates up through `Repl.start()` uncaught and is
  caught by `repl()`'s wrapping `try/except KeyboardInterrupt`, which
  prints `"\nInterrupted."` and (via `finally`) still closes the logger.
  `Repl.start()` itself has no interrupt handling of its own, matching
  Ruby's `Repl#start` (no `rescue Interrupt` inside the class).
- **`client.py`'s 401 check is inserted at the same point as Ruby's** —
  inside the "response wasn't a success" branch, checked *before* the
  generic failure message, so a 401 gets the specific
  `"authentication failed (401) — check your API key"` message instead of
  the generic `"API request failed after N attempts (401): <body>"` one.
- **`VERSION` lives in its own `version.py`, matching Ruby's dedicated
  `version.rb`.** A one-line module: `VERSION = "0.8.0"`. Imported into
  `boukensha/__init__.py` and threaded into `Repl(version=VERSION, ...)`
  inside `repl()`, exactly mirroring `lib/boukensha.rb`'s
  `require_relative "boukensha/version"` + `version: VERSION`.
- **`repl.py` imports `boukensha` at module scope for `quiet()`/`loud()`,
  the same lazy-safe circular-import pattern already established in
  `logger.py` since `06`.** `boukensha/__init__.py` does `from .repl
  import Repl`; `repl.py` needs `boukensha.quiet()`/`boukensha.loud()`
  (called from inside `Repl.start`'s command handling, at session-run
  time, never at import time), so `import boukensha` at the top of
  `repl.py` is safe for the same reason it was safe in `logger.py` — the
  attribute access happens long after `boukensha/__init__.py` has finished
  executing.

## Target file layout

```
week1_baseline/python/08_the_repl_loop/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # new — documents actual Logger.turn()/banner/transcript behavior, not the stale Ruby doc
  prompts/
    system.md                      # unchanged from 07_the_run_dsl
  boukensha/
    __init__.py                    # adds repl(), imports Repl and VERSION
    version.py                     # new: VERSION = "0.8.0"
    config.py                      # updated: _resolve_dir gains the CWD/.boukensha tier
    tool.py                        # unchanged from 07_the_run_dsl
    message.py                     # unchanged from 07_the_run_dsl
    context.py                     # updated: adds clear_messages()
    errors.py                      # unchanged from 07_the_run_dsl
    registry.py                    # unchanged from 07_the_run_dsl
    prompt_builder.py              # unchanged from 07_the_run_dsl
    client.py                      # updated: specific ApiError message for 401 responses
    logger.py                      # unchanged from 07_the_run_dsl (turn()/subscribe() already exist since 07)
    agent.py                       # updated: persists the final reply into context on every return path
    run_dsl.py                     # unchanged from 07_the_run_dsl
    repl.py                        # new: Repl
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
    example.py                     # rewritten: calls boukensha.repl(block=register); tools point at ../../07_the_run_dsl
week1_baseline/bin/python/08_the_repl_loop   # already exists — see Open Questions re: BOUKENSHA_DIR export
```

## Porting notes (Ruby → Python mapping)

### `version.py` (new)

```python
VERSION = "0.8.0"
```

### `context.py` — `clear_messages()`

```python
def clear_messages(self):
    """Drop all conversation history, keeping tools and system prompt
    intact. Used by the REPL's /clear command."""
    self.messages = []
```

(Ruby's `!` suffix convention has no Python equivalent — dropped, same
convention already established across this series, e.g. `prompt_override?`
→ `is_prompt_override` in `00`.)

### `client.py` — specific 401 message

```python
if not (200 <= response_code < 300):
    if response_code == 401:
        raise ApiError("authentication failed (401) — check your API key")

    suffix = "" if attempts == 1 else "s"
    raise ApiError(
        f"API request failed after {attempts} attempt{suffix} "
        f"({response_code}): {response_body.decode('utf-8', errors='replace')}"
    )
```

### `config.py` — three-tier `_resolve_dir`

```python
def _resolve_dir(self):
    # 1. Explicit override
    if os.environ.get("BOUKENSHA_DIR"):
        return str(Path(os.environ["BOUKENSHA_DIR"]).expanduser().resolve())

    # 2. .boukensha in the current working directory
    cwd_dir = Path.cwd() / ".boukensha"
    if cwd_dir.is_dir():
        return str(cwd_dir)

    # 3. ~/.boukensha default
    return str(Path(self.DEFAULT_DIR).expanduser().resolve())
```

### `agent.py` — persist the final reply

Three call sites gain one line each, right before their `return`:

```python
# run(), normal completion branch
text = self._extract_text(parsed["content"])
self._log_response(text=text, response=response)
self.logger.turn_end(reason="completed", iterations=self.iteration)
self.context.add_message("assistant", text)
return text

# _wrap_up(), success branch
...
self._log_response(text=text, response=response)
self.logger.turn_end(reason=reason, iterations=self.iteration)
self.context.add_message("assistant", text)
return text

# _wrap_up(), except ApiError branch
except ApiError:
    msg = self._fallback_message(reason)
    self.logger.turn_end(reason=reason, iterations=self.iteration)
    self.context.add_message("assistant", msg)
    return msg
```

Everything else in `agent.py` — the tool-use branch, `_handle_tool_calls`,
`_call_opts`, iteration/output-token resolution — is unchanged from `07`.

### `repl.py` (new) — `Repl`

```python
import os
import sys

import boukensha
from .agent import Agent
from .errors import ApiError, LoopError


class Repl:
    """The interactive session loop.

    Wraps the same primitives as a single boukensha.run() call, but instead
    of running once it stays alive: it reads a task from the user, runs the
    agent, prints the reply, and loops back to the prompt.

    The Context is shared across every turn so conversation history
    accumulates naturally — the agent sees the full transcript each time
    it is called.
    """

    PROMPT = "boukensha> "
    HELP = (
        "Commands:\n"
        "  /quiet   suppress logging output\n"
        "  /loud    re-enable logging output\n"
        "  /clear   wipe conversation history (tools stay)\n"
        "  /exit    leave the REPL\n"
        "  /help    show this message"
    )

    def __init__(self, context, registry, builder, client, logger, config_dir=None,
                 provider=None, model=None, version=None, api_key=None,
                 task_settings=None, max_iterations=None, max_output_tokens=None):
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.logger = logger
        self.task_settings = task_settings
        self.max_iterations = max_iterations
        self.max_output_tokens = max_output_tokens
        self.config_dir = config_dir
        self.provider = provider
        self.model = model
        self.version = version
        self.api_key = api_key
        self.turn = 0

    def start(self):
        print(self._banner(), end="")

        while True:
            sys.stdout.write(self.PROMPT)
            sys.stdout.flush()

            line = sys.stdin.readline()
            if not line:
                break  # EOF / Ctrl-D

            user_input = line.strip()
            if not user_input:
                continue

            if user_input in ("/exit", "/quit"):
                print("Goodbye.")
                break
            elif user_input == "/help":
                print(self.HELP)
                continue
            elif user_input == "/quiet":
                boukensha.quiet()
                print("(logging suppressed — type /loud to re-enable)")
                continue
            elif user_input == "/loud":
                boukensha.loud()
                print("(logging enabled)")
                continue
            elif user_input == "/clear":
                self.context.clear_messages()
                self.turn = 0
                print("(conversation history cleared)")
                continue

            self._run_turn(user_input)

    def _banner(self):
        if self.api_key is None or not self.api_key.strip():
            key_status = "✗ API key not set"
        else:
            key_status = "✓ API key set"
        provider_line = f"{self.provider or 'default'} ({self.model or 'default'})  {key_status}"
        config_exists = bool(self.config_dir) and os.path.isdir(self.config_dir)
        config_line = self.config_dir if config_exists else f"{self.config_dir or '(default)'}  ✗ directory not found"
        ver = self.version or "?.?.?"
        padding = " " * (9 - len(ver))

        return (
            "\n"
            "╔══════════════════════════════════════╗\n"
            f"║  BOUKENSHA MUD Assistant (v{ver}){padding}║\n"
            "╚══════════════════════════════════════╝\n"
            f"  config:    {config_line}\n"
            f"  provider:  {provider_line}\n"
            "\n"
            "  /quiet or /loud   toggle logging\n"
            "  /clear           reset conversation history\n"
            "  /exit or /quit    leave the REPL\n"
            "\n"
        )

    def _run_turn(self, user_input):
        try:
            self.turn += 1
            self.logger.turn(n=self.turn)

            self.context.add_message("user", user_input)

            agent = Agent(
                context=self.context, registry=self.registry, builder=self.builder,
                client=self.client, logger=self.logger, task_settings=self.task_settings,
                max_iterations=self.max_iterations, max_output_tokens=self.max_output_tokens,
            )
            result = agent.run()

            # Print the final response outside of the logger so it is
            # always visible, even when boukensha.quiet() is active.
            print()
            print(result)
        except LoopError as e:
            print(f"\n[error] {e}")
        except ApiError as e:
            print(f"\n[error] API call failed: {e}")
```

### `boukensha/__init__.py` — `repl()`

```python
from .repl import Repl
from .version import VERSION

# ... (existing imports/state/run() unchanged) ...

def repl(system=None, model=None, backend=None, api_key=None,
         ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    """Interactive REPL: register tools once, then loop — reading tasks
    from stdin, running the agent, and printing replies — until the user
    types /exit or sends EOF.

    Conversation history accumulates across every turn so the agent always
    sees the full transcript.

    Same arguments as run(), minus `task` (the user supplies tasks
    interactively).
    """
    logger = None
    try:
        cfg = config()
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

        Repl(
            context=ctx, registry=registry, builder=builder, client=client, logger=logger,
            task_settings=task_settings, max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens, config_dir=cfg.dir,
            provider=backend, model=model, version=VERSION, api_key=api_key,
        ).start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger is not None:
            logger.close()
```

`__all__` gains `"Repl"` and `"VERSION"`, plus `"repl"`.

### Example (`example.rb` → `examples/example.py`)

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boukensha

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically (or,
# since this step, any .boukensha/ found in the current working directory).
os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

print(f"Config: {boukensha.config()}")
print()

# The base directory tools will operate relative to — 07_the_run_dsl makes
# a good playground since it already has source files to read.
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "07_the_run_dsl"


def register(dsl):
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "File path (relative to the working directory)"}},
        block=lambda path: Path(BASE_DIR, path).read_text(),
    )
    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "Directory path (relative to the working directory, or '.' for root)"}},
        block=lambda path: ", ".join(
            sorted(entry for entry in os.listdir(Path(BASE_DIR, path)) if not entry.startswith("."))
        ),
    )


boukensha.repl(block=register)
```

Note the `.sort` in Ruby's `list_directory` block
(`Dir.entries(...).reject { ... }.sort.join(", ")`) — `04`'s/`05`'s Python
`os.listdir` version never sorted; this step's Ruby source adds `.sort`,
so the Python port adds `sorted(...)` to match, rather than silently
carrying forward the older unsorted behavior.

### `README.md`

New file, following the Python README structure established in `00`-`07`:

- Overview / before-and-after table (`run()` vs `repl()`: one turn vs
  many, history discarded vs accumulated, no stdin interaction vs a
  prompt).
- **New Files** table: `boukensha/repl.py`, `boukensha/version.py`.
  **Updated Files** table: `boukensha/__init__.py` (`repl()`),
  `boukensha/agent.py` (persists final reply), `boukensha/context.py`
  (`clear_messages()`), `boukensha/config.py` (CWD `.boukensha` tier),
  `boukensha/client.py` (401 message).
- **`boukensha.Repl`** section — built-in commands table, matching the
  code's actual behavior (including the `/quiet`/`/loud` caveat that
  they're currently cosmetic-only — see Design Considerations).
- **`boukensha.repl()`** section — same shape as `06`'s `run()` doc, minus
  `task`.
- **What It Looks Like** — a real captured transcript from running the
  example (banner + a couple of turns + `/exit`), not the Ruby README's
  illustrative sample.
- **Considerations** — carried forward from `07` where still accurate
  (assistant-before-tool-result ordering, multi-tool-call turns,
  `max_iterations` as a per-turn ceiling — now explicitly per-turn since
  each turn gets a fresh `Agent`), plus a new one specific to this step:
  the final-reply persistence change and why it matters for follow-up
  questions.
- **Run Example** pointing at `./week1_baseline/bin/python/08_the_repl_loop`,
  noting it's interactive (reads from stdin).

## Cleanup

Nothing to clean up — fresh directory, no leftover `__pycache__` from a
prior stale copy. Standard `__pycache__` cleanup after the verification run
still applies (gitignored, but tidy).

## Configuration Schema

Unchanged from `07` — `repl()` introduces no new `settings.yaml` keys:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
    max_iterations: 25        # optional, defaults to 25 — now a per-turn ceiling
    max_output_tokens: 1024   # optional, defaults to 1024
```

## Open Questions

1. **Should `bin/python/08_the_repl_loop` export `BOUKENSHA_DIR` the way
   Ruby's launcher now does, instead of keeping the override inside
   `example.py`?** As detailed in Design Considerations, this plan keeps
   `example.py`'s override (matching every prior Python step) rather than
   moving it to the launcher (matching Ruby's actual `07`→`08`
   structural change), specifically because the launcher already exists
   and doesn't currently export it. Recommendation: leave it as proposed
   (safer, no launcher changes) unless matching Ruby's exact
   responsibility-split is preferred — flagging since it's a real
   structural choice made in the reference, not just an implementation
   detail.
2. **Verification requires an interactive stdin session**, unlike every
   prior step's single non-interactive run. The REPL loop reads from
   `sys.stdin` in a `while True` loop — verifying it end-to-end means
   either driving it with piped input (e.g. `printf '...\n/exit\n' |
   ./week1_baseline/bin/python/08_the_repl_loop`) or a short interactive
   session. Piped input is the more reproducible option and is what this
   plan intends to use for the verification run.
3. **This step still makes real API calls per turn**, inherited from
   `05`-`07` — each verification turn is a real, if trivial, Haiku-tier
   request. A short scripted verification (2-3 turns via piped stdin) is
   assumed rather than an extended interactive session.
