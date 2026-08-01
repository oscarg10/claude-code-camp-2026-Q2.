# Python Port Plan — 01 · Struct Skeleton

## Goal

Port `week1_baseline/ruby/01_struct_skeleton` to Python as
`week1_baseline/python/01_struct_skeleton` (name kept as-is, matching the
existing directory and its `bin/ruby/01_struct_skeleton` launcher — a known
typo for "struct" that we're intentionally not fixing here). This step adds
three data structures on top of the `00_config` port: `Tool`, `Message`, and
`Context`.

## Starting state (found during planning)

`week1_baseline/python/01_struct_skeleton/` already exists but is an
**unmodified copy of the `00_config` port** — it still prints
`"Boukensha Step 0: Configuration"` and has none of the `Tool`/`Message`/
`Context` work. Two bugs came along with the copy and need fixing as part of
this port, not carried forward:

- Duplicate example files: both `examples/example.py` and `examples/examples.py`
  exist (same issue we hit and fixed in `00_config`). Keep `example.py` only
  — it's what the launcher script runs.
- `examples/example.py` calls `Player.prompt_override(...)`, but `base.py`
  only defines `is_prompt_override` (the `examples.py` duplicate has the
  correct call). This is exactly the naming-convention decision made in the
  `00_config` plan — apply it consistently, not re-litigate it.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/01_struct_skeleton/README.md` | Spec/behaviour doc — data structure field tables and `to_s` examples below are ported from here |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/tool.rb` | `Boukensha::Tool` — a `Struct.new(:name, :description, :parameters, :block)` with custom `to_s` |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/message.rb` | `Boukensha::Message` — a `Struct.new(:role, :content, :tool_use_id)` with custom `to_s` |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/context.rb` | `Boukensha::Context` — holds `task`, `system`, `messages`, `tools`; `register_tool`, `add_message`, `tool_count`, `turn_count`, `to_s` |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/config.rb` | Same as `00_config`'s, **minus** the `PROMPTS_DIR` constant (this step dropped the shipped default prompt — see Porting notes) |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/tasks/base.rb` | Unchanged from `00_config` (diffed — identical) |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha/tasks/player.rb` | Unchanged from `00_config` (diffed — identical) |
| `week1_baseline/ruby/01_struct_skeleton/lib/boukensha.rb` | Top-level require — now also requires `tool`, `message`, `context` |
| `week1_baseline/ruby/01_struct_skeleton/examples/example.rb` | Runnable smoke-test — builds a `Context`, registers a `move` tool, adds two messages, prints everything. Port line-for-line. |
| `week1_baseline/ruby/01_struct_skeleton/Gemfile` | Still just `dotenv` — no new dependency for this step |

Also reference the already-completed `00_config` port
(`week1_baseline/python/00_config/`) for the established Python conventions:
`is_prompt_override` naming, `#<...>`-style `__str__` for parity, single
`example.py` (no `examples.py`), shared root `.venv`.

## Design Considerations

- **Structs → `@dataclass`.** Ruby's `Struct.new(...) do ... end` pattern
  (positional fields + a custom `to_s` block) maps cleanly onto Python's
  `@dataclass` with fields in the same order and a `__str__` override. No
  need for `attrs` or anything heavier — this is a direct 1:1 structural
  match, same "no new dependency" philosophy as `00_config`.
- **`Tool.block` — a plain callable.** Ruby's `->(direction) { ... }` lambda
  becomes a Python `lambda direction: ...`. `Tool.parameters` stays a plain
  `dict` (no schema validation layer), matching `00_config`'s "plain dict,
  no Pydantic" decision.
- **Symbol-keyed `to_s` output changes shape, and that's expected.** Ruby's
  `parameters.keys` on a hash with symbol keys prints as `[:direction]`
  (Ruby's inspect format for arrays of symbols). Python has no symbol type,
  so `list(parameters.keys())` on a string-keyed dict prints as
  `['direction']`. Don't try to fake symbol-style output — this is a
  natural, expected divergence from a 1:1 port, same category as the
  string/symbol-duality note already made in the `00_config` plan.
- **`task&.task_name` → guarded call.** Ruby's safe-navigation operator on
  `Context#to_s` becomes `self.task.task_name() if self.task else None` in
  Python. `task` here is the *class* (`Player`), not an instance —
  `task_name` stays a classmethod call.
- **No `PROMPTS_DIR` / `default_prompts_dir` in this step.** The Ruby
  `config.rb` for this step dropped the `PROMPTS_DIR` constant, and
  `example.rb` calls `system_prompt` without `default_prompts_dir:`. There's
  also no `prompts/system.md` shipped in the Ruby `01_struct_skeleton`
  folder at all. Port this faithfully: drop `Config.PROMPTS_DIR`, don't pass
  `default_prompts_dir` from the example, and don't ship a `prompts/`
  directory in the Python port either. (The system prompt in the smoke test
  comes entirely from the user's own `.boukensha/prompts/player/system.md`
  override — if that's missing, `system_prompt` is `None`, which is
  expected/acceptable for this step.)
- **Folder layout: snapshot per step**, unchanged approach from `00_config`
  — `python/01_struct_skeleton/` is self-contained, copying forward
  `config.py`/`tasks/` and adding the three new modules.

## Target file layout

```
week1_baseline/python/01_struct_skeleton/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # ported from the Ruby README, Python-flavoured examples
  boukensha/
    __init__.py                    # exports Config, Player, Tool, Message, Context
    config.py                      # same as 00_config's, minus PROMPTS_DIR
    tool.py                        # Tool dataclass
    message.py                     # Message dataclass
    context.py                     # Context class
    tasks/
      __init__.py
      base.py                      # unchanged from 00_config
      player.py                    # unchanged from 00_config
  examples/
    example.py                     # port of examples/example.rb (single file — delete examples.py)
week1_baseline/bin/python/01_struct_skeleton   # new launcher, mirrors bin/python/00_config
```

## Porting notes (Ruby → Python mapping)

### `Tool` (`tool.rb` → `tool.py`)

```ruby
Tool = Struct.new(:name, :description, :parameters, :block) do
  def to_s
    "#<Tool name=#{name} description=#{description.to_s[0..40]} params=#{parameters.keys}>"
  end
end
```

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    block: callable

    def __str__(self):
        return f"#<Tool name={self.name} description={self.description[:41]} params={list(self.parameters.keys())}>"
```

Note `description.to_s[0..40]` is 41 characters (inclusive range) → Python
slice `[:41]`.

### `Message` (`message.rb` → `message.py`)

```ruby
Message = Struct.new(:role, :content, :tool_use_id) do
  def to_s
    id_tag = tool_use_id ? " [#{tool_use_id}]" : ""
    "#<Message role=#{role}#{id_tag} content=#{content.to_s[0..60]}...>"
  end
end
```

```python
@dataclass
class Message:
    role: str
    content: str
    tool_use_id: str | None = None

    def __str__(self):
        id_tag = f" [{self.tool_use_id}]" if self.tool_use_id else ""
        return f"#<Message role={self.role}{id_tag} content={self.content[:61]}...>"
```

`content.to_s[0..60]` is 61 characters → Python slice `[:61]`.

### `Context` (`context.rb` → `context.py`)

```ruby
class Context
  attr_reader :task, :system, :messages, :tools

  def initialize(task:, system: nil)
    @task, @system, @messages, @tools = task, system, [], {}
  end

  def register_tool(tool) = @tools[tool.name] = tool
  def add_message(role, content, tool_use_id: nil) = @messages << Message.new(role, content, tool_use_id)
  def tool_count = @tools.size
  def turn_count = @messages.size
  def to_s = "#<Context task=#{task&.task_name} turns=#{turn_count} tools=#{tool_count}>"
end
```

```python
class Context:
    def __init__(self, task, system=None):
        self.task = task
        self.system = system
        self.messages = []
        self.tools = {}

    def register_tool(self, tool):
        self.tools[tool.name] = tool

    def add_message(self, role, content, tool_use_id=None):
        self.messages.append(Message(role, content, tool_use_id))

    @property
    def tool_count(self):
        return len(self.tools)

    @property
    def turn_count(self):
        return len(self.messages)

    def __str__(self):
        task_name = self.task.task_name() if self.task else None
        return f"#<Context task={task_name} turns={self.turn_count} tools={self.tool_count}>"
```

### `Config` (`config.py`, carried forward)

Copy `00_config`'s `config.py` verbatim, **except** remove the
`PROMPTS_DIR` class attribute — it doesn't exist in this step's Ruby
`config.rb` and nothing in this step's example references it.

### `Tasks::Base` / `Tasks::Player`

Unchanged from `00_config` — the Ruby files diffed identical. Copy
`tasks/base.py` and `tasks/player.py` forward as-is, including the
`is_prompt_override` naming already established.

### `boukensha/__init__.py`

Mirrors the expanded `lib/boukensha.rb`, which now also requires `tool`,
`message`, `context`:

```python
from .config import Config
from .tasks.player import Player
from .tool import Tool
from .message import Message
from .context import Context

__all__ = ["Config", "Player", "Tool", "Message", "Context"]
```

### Example (`example.rb` → `examples/example.py`)

Port every `puts` line 1:1:

```python
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(player_settings, user_prompts_dir=config.user_prompts_dir)

ctx = Context(task=Player, system=system_prompt)

ctx.register_tool(Tool(
    "move",
    "Move the player in a direction (north, south, east, west, up, down)",
    {"direction": {"type": "string", "description": "The direction to move"}},
    lambda direction: f"You move {direction} into a torch-lit corridor.",
))

ctx.add_message("user", "Explore north and tell me what you find.")
ctx.add_message("assistant", "Sure, let me head north and take a look.")

print("=== Boukensha Step 1: Struct Skeleton ===")
print()
print(f"Config:   {config}")
print(f"Context:  {ctx}")
print(f"Tool:     {ctx.tools['move']}")
print("Messages:")
for m in ctx.messages:
    print(f"  {m}")
```

Note `system_prompt` is called **without** `default_prompts_dir=` here,
matching the Ruby example — see Design Considerations above.

The `BOUKENSHA_DIR` override at the top of the file (resolving to the repo
root `.boukensha/`) carries forward unchanged from the `00_config` example,
using the same `parents[4]` depth (the directory nesting from
`examples/example.py` to the repo root is the same as in `00_config`).

### Launcher (`bin/python/01_struct_skeleton`, new)

Mirror `bin/python/00_config` exactly, pointing at the new step directory:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
cd "$SCRIPT_DIR/../../python/01_struct_skeleton"
"$REPO_ROOT/.venv/bin/python" examples/example.py
```

## Also fix while here: `bin/ruby/00_config`

Left over from the `bin/` restructure (subfolders `bin/python/` and
`bin/ruby/` were introduced, per the prior plan's open question), this
script was moved into `bin/ruby/` without updating its relative path — it
still does `cd "$(dirname "$0")/../00_config"` (one level too shallow,
lands on the nonexistent `bin/00_config`). This was flagged as an open TODO
in the `00_config` plan and never fixed. `bin/ruby/01_struct_skeleton`
already has the correct pattern — apply the same fix:

```bash
#!/usr/bin/env bash

cd "$(dirname "$0")/../../ruby/00_config"
bundle exec ruby examples/example.rb
```

## Cleanup

- Delete `examples/examples.py` (stray duplicate, see Starting state).
- Delete the `__pycache__/` directories currently sitting in
  `python/01_struct_skeleton/` (leftover from running the stale copy) —
  regenerated automatically, not meant to be tracked.

## Configuration Schema

Unchanged — this step doesn't touch `settings.yaml` or `.env` format. Same
schema as documented in the `00_config` plan.

## Acceptance

Run `week1_baseline/bin/python/01_struct_skeleton` and confirm the output
shape matches `bundle exec ruby examples/example.rb` run from
`week1_baseline/ruby/01_struct_skeleton` (adjusted for real values from the
user's `.boukensha/`), e.g.:

```
=== Boukensha Step 1: Struct Skeleton ===

Config:   #<Boukensha::Config dir=... tasks=player>
Context:  #<Context task=player turns=2 tools=1>
Tool:     #<Tool name=move description=Move the player in a direction (north, so params=['direction']>
Messages:
  #<Message role=user content=Explore north and tell me what you find....>
  #<Message role=assistant content=Sure, let me head north and take a look....>
```
