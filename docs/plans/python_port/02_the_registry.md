# Python Port Plan — 02 · The Registry

## Goal

Port `week1_baseline/ruby/02_the_registry` to Python, replacing the contents
of `week1_baseline/python/02_the_registry`. This step adds a `Registry`
class on top of the `01_struct_skeleton` port: tools are now registered
through `registry.tool(...)` instead of directly on the `Context`, and can
be looked up and invoked by name via `registry.dispatch(...)`. It also adds
BOUKENSHA's first custom error class, `UnknownToolError`.

## Starting state (found during planning)

`week1_baseline/python/02_the_registry/` currently exists but is an
**unmodified copy of the `01_struct_skeleton` port** — same bug pattern
called out in the `01_struct_skeleton` plan when porting from `00_config`:

- `README.md` is titled "01 · The Struct Skeleton (Python)" and documents
  `Tool`/`Message`/`Context` only — no mention of `Registry` or
  `UnknownToolError`.
- `examples/example.py` prints `"=== Boukensha Step 1: Struct Skeleton ==="`,
  registers its one tool directly on `ctx` (`ctx.register_tool(...)`), and
  never calls `dispatch`.
- There is no `registry.py` or `errors.py` under `boukensha/`, and
  `boukensha/__init__.py` doesn't export `Registry` or `UnknownToolError`.
- `week1_baseline/bin/python/02_the_registry` still `cd`s into
  `python/01_struct_skeleton` and is otherwise byte-identical to
  `bin/python/01_struct_skeleton` — it currently runs the wrong step.

None of this is step-02-specific work carried over from Ruby; it's leftover
copy-paste that needs replacing, same as the `01_struct_skeleton` starting
state.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/02_the_registry/README.md` | Spec/behaviour doc — the `Registry` API table, `UnknownToolError` description, and expected output below are ported from here |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/registry.rb` | `Boukensha::Registry` — `initialize(context)`, `tool(name, description:, parameters:, &block)`, `dispatch(name, args = {})` |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/errors.rb` | `Boukensha::UnknownToolError < StandardError` — the only new error class |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/tool.rb` | Unchanged from `01_struct_skeleton` (diffed — identical) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/message.rb` | Unchanged from `01_struct_skeleton` (diffed — identical) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/context.rb` | Unchanged from `01_struct_skeleton` (diffed — identical) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/config.rb` | Unchanged from `01_struct_skeleton` (diffed — identical; still no `PROMPTS_DIR`) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/tasks/base.rb` | Unchanged (diffed — identical) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha/tasks/player.rb` | Unchanged (diffed — identical) |
| `week1_baseline/ruby/02_the_registry/lib/boukensha.rb` | Top-level require — now also requires `errors` and `registry` |
| `week1_baseline/ruby/02_the_registry/examples/example.rb` | Runnable smoke-test — builds a `Context` + `Registry`, registers `move` and `shout` tools through the registry, dispatches both by name, then dispatches an unknown tool and rescues `UnknownToolError`. Port line-for-line. |
| `week1_baseline/ruby/02_the_registry/Gemfile` | Still just `dotenv` — no new dependency for this step |

Also reference the already-completed `01_struct_skeleton` port
(`week1_baseline/python/01_struct_skeleton/`, once restored to its own
correct content — see Starting state) for established Python conventions:
`is_prompt_override` naming, `#<...>`-style `__str__` for parity, single
`example.py`, shared root `.venv`.

## Design Considerations

- **`Registry` as a plain class wrapping a `Context`.** Direct 1:1 port —
  `Registry.__init__(self, context)` stores the context; no new state of
  its own. Same "thin wrapper, no framework" philosophy as every prior
  step.
- **No Ruby block syntax — pass the callable as an explicit `block` keyword
  argument.** Ruby's `registry.tool(name, description:, parameters:, &block)`
  takes the tool body as a trailing block. Python has no equivalent trailing
  block syntax, so the callable becomes a normal keyword argument, matching
  how `Tool` itself already takes `block` as its fourth field in the
  `01_struct_skeleton` port:

  ```python
  registry.tool(
      "move",
      description="Move the player in a direction (north, south, east, west, up, down)",
      parameters={"direction": {"type": "string"}},
      block=lambda direction: f"You move {direction} into a torch-lit corridor.",
  )
  ```

  This keeps `description=`/`parameters=`/`block=` all keyword args, closest
  in shape to the Ruby call site's `description:`/`parameters:` keywords
  plus trailing block.
- **`dispatch`'s symbol-conversion step has no Python equivalent — and
  that's expected, not a gap.** Ruby's `dispatch` does
  `tool.block.call(**args.transform_keys(&:to_sym))` because Ruby keyword
  arguments must be symbols, but `args` arrives as a string-keyed hash (the
  README's own "Considerations" section calls this out as the
  string-vs-symbol gotcha the step exists to teach). Python keyword
  arguments are always strings under the hood, so `tool.block(**args)`
  needs no conversion step at all. Port `dispatch` without a translation
  line, and note in the Python README (see below) that this divergence is
  the direct Python-side answer to the same lesson the Ruby README teaches
  — not a corner being cut.
- **`UnknownToolError` — a plain `Exception` subclass.** Ruby's
  `StandardError` subclass maps to Python's `Exception` (no need to reach
  for a narrower builtin base — every other custom error in this codebase
  so far has been this same flat shape). One class, one file, matching
  `errors.rb`'s layout 1:1.
- **Tool lookup key stays a plain string.** Ruby's `@context.tools[name.to_s]`
  guards against a caller passing a symbol; Python has no symbol type, so
  `self.context.tools[str(name)]` is the direct equivalent guard (handles a
  caller passing something non-string-but-string-like) without the
  string/symbol duality that motivated it in Ruby.
- **Folder layout: snapshot per step**, unchanged approach — the existing
  (currently mis-copied) `python/02_the_registry/` directory gets
  overwritten in place with `01_struct_skeleton`'s files plus this step's
  additions, rather than deleted and recreated, so the directory itself
  doesn't need to move.

## Target file layout

```
week1_baseline/python/02_the_registry/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # rewritten for this step (currently copy of 01's)
  boukensha/
    __init__.py                    # exports Config, Player, Tool, Message, Context, Registry, UnknownToolError
    config.py                      # unchanged from 01_struct_skeleton
    tool.py                        # unchanged from 01_struct_skeleton
    message.py                     # unchanged from 01_struct_skeleton
    context.py                     # unchanged from 01_struct_skeleton
    errors.py                      # new: UnknownToolError
    registry.py                    # new: Registry
    tasks/
      __init__.py
      base.py                      # unchanged from 01_struct_skeleton
      player.py                    # unchanged from 01_struct_skeleton
  examples/
    example.py                     # rewritten for this step (currently copy of 01's)
week1_baseline/bin/python/02_the_registry   # fixed to point at 02_the_registry, not 01
```

## Porting notes (Ruby → Python mapping)

### `UnknownToolError` (`errors.rb` → `errors.py`)

```ruby
module Boukensha
  class UnknownToolError < StandardError; end
end
```

```python
class UnknownToolError(Exception):
    pass
```

### `Registry` (`registry.rb` → `registry.py`)

```ruby
class Registry
  def initialize(context)
    @context = context
  end

  def tool(name, description:, parameters: {}, &block)
    tool = Tool.new(name.to_s, description, parameters, block)
    @context.register_tool(tool)
    tool
  end

  def dispatch(name, args = {})
    tool = @context.tools[name.to_s]
    raise UnknownToolError, "No tool registered as '#{name}'" unless tool
    tool.block.call(**args.transform_keys(&:to_sym))
  end
end
```

```python
from .errors import UnknownToolError
from .tool import Tool


class Registry:
    def __init__(self, context):
        self.context = context

    def tool(self, name, description, parameters=None, block=None):
        tool = Tool(str(name), description, parameters or {}, block)
        self.context.register_tool(tool)
        return tool

    def dispatch(self, name, args=None):
        tool = self.context.tools.get(str(name))
        if tool is None:
            raise UnknownToolError(f"No tool registered as '{name}'")
        return tool.block(**(args or {}))
```

### `boukensha/__init__.py`

Mirrors the expanded `lib/boukensha.rb`, which now also requires `errors`
and `registry`:

```python
from .config import Config
from .context import Context
from .errors import UnknownToolError
from .message import Message
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

__all__ = ["Config", "Player", "Tool", "Message", "Context", "Registry", "UnknownToolError"]
```

### Example (`example.rb` → `examples/example.py`)

Port every `puts` line 1:1, including the trailing `begin`/`rescue` block as
a `try`/`except`:

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boukensha import Config, Context, Player, Registry, UnknownToolError

os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(player_settings, user_prompts_dir=config.user_prompts_dir)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

# Notice that we now register the tools through the registry instead of directly
# on the context in the previous step.
# They will still be attached to context which is why we pass it into
# our registry when we initialize it.
registry.tool(
    "move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string"}},
    block=lambda direction: f"You move {direction} into a torch-lit corridor.",
)

registry.tool(
    "shout",
    description="Shout a message so everyone in the zone can hear it",
    parameters={"message": {"type": "string"}},
    block=lambda message: message.upper(),
)

print("=== Boukensha Step 2: Tool Registry ===")
print()
print(f"Config:  {config}")
print(f"Context: {ctx}")
print("Tools:")
for t in ctx.tools.values():
    print(f"  {t}")
print()

# Here we are mimicking what the agent would do when
# it needs to call a tool from the registry. We are
# still missing the actual code that would decide when
# to call the registry for a tool.
print("Dispatching 'shout' with message='dragon spotted'...")
result = registry.dispatch("shout", {"message": "dragon spotted"})
print(f"Result: {result}")
print()

print("Dispatching 'move' with direction='north'...")
result = registry.dispatch("move", {"direction": "north"})
print(f"Result: {result}")
print()

try:
    registry.dispatch("flee")
except UnknownToolError as e:
    print(f"UnknownToolError caught: {e}")
```

Note `message.upcase` → `message.upper()`, the one non-mechanical line in
the port.

### `README.md`

Rewritten for this step, following the `01_struct_skeleton` Python README's
structure (Setup / data structures / Config resolution / Run Example /
Considerations / Naming conventions), replacing its `Tool`/`Message`/
`Context` section with:

- A `Registry` section documenting `tool(...)` and `dispatch(...)`, mirroring
  the Ruby README's method table.
- An `UnknownToolError` section with the same example message.
- A **Considerations** entry explaining the symbol/string dispatch
  divergence called out above (Python's `dispatch` needs no key-translation
  step — the lesson the Ruby step teaches has no analogue to port, and the
  README should say so rather than silently omitting it).
- Updated **Run Example** pointing at `./week1_baseline/bin/python/02_the_registry`.

### Launcher (`bin/python/02_the_registry`, fixed)

Currently identical to `bin/python/01_struct_skeleton` (wrong target dir —
see Starting state). Fix to match the established per-step pattern:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
cd "$SCRIPT_DIR/../../python/02_the_registry"
"$REPO_ROOT/.venv/bin/python" examples/example.py
```

## Cleanup

- Delete any stray `__pycache__/` directories currently sitting in
  `python/02_the_registry/` (leftover from running the stale `01`-copy).

## Configuration Schema

Unchanged — this step doesn't touch `settings.yaml` or `.env` format. Same
schema as documented in the `00_config` plan.

## Open Questions

1. **README "Expected Output" block doesn't match `Context#to_s`.** The
   Ruby README's expected output shows:
   ```
   Context: #<Context turns=0 tools=2 budget=8192>
   ```
   but the actual `context.rb` in this step (identical to `01_struct_skeleton`'s)
   has no `budget` attribute and its `to_s` includes `task=...`, so the real
   output is closer to `#<Context task=player turns=0 tools=2>`. This looks
   like a leftover from a later, not-yet-ported step's README rather than
   something this step's code actually produces. Recommendation: write the
   Python README's expected output using what the ported code actually
   prints (`task=player turns=0 tools=2`, no `budget`), and leave a short
   note that the Ruby README's sample output doesn't match its own step's
   code — don't try to fabricate a `budget` field to match it. Confirm
   before implementation, since it affects what the acceptance check
   compares against.
