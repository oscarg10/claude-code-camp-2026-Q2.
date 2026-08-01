# 02 · The Tool Registry (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/02_the_registry/requirements.txt
```

The launcher at `week1_baseline/bin/python/02_the_registry` assumes
`.venv` already exists at the repo root and has these dependencies
installed.

---

The Tool Registry is how BOUKENSHA manages what capabilities the agent can use.

It has two jobs:
  1. storing tools
  2. dispatching tools when asked

## How It Works

The agent NEVER calls a tool directly.
It emits a structured request (name and args) and the Registry looks up the tool and runs it.

```
Agent:    "Hey registry call move with direction='north'"
Registry: "looking up "move" in the tool table"
Registry: "Found it now calling the block with the provided args"
Registry: "Here's the result"
Agent:    "Thanks buddy"
Registry: "Thats why you pay me the big tokes"
```

## `boukensha.Registry`

| Method | Description |
|---|---|
| `tool(name, description, parameters=None, block=None)` | Registers a new tool on the context |
| `dispatch(name, args=None)` | Looks up a tool by name and calls it with the provided args |

Ruby passes the tool's implementation as a trailing block
(`registry.tool(name, description:, parameters:) { ... }`). Python has no
trailing-block syntax, so the callable is passed explicitly as the `block`
keyword argument instead:

```python
registry.tool(
    "move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string"}},
    block=lambda direction: f"You move {direction} into a torch-lit corridor.",
)
```

## `boukensha.UnknownToolError`

Raised when `dispatch` is called with a name that has no registered tool.
A harness needs explicit error boundaries — an unrecognised tool name should
never silently fail.

**Example:**
```
UnknownToolError: No tool registered as 'flee'
```

## Data Structures

Unchanged from `01_struct_skeleton`:
- `boukensha.Tool`
- `boukensha.Message`
- `boukensha.Context`

## Config directory resolution

Unchanged from `00_config` — the class looks for a `.boukensha/` directory
in this order:

1. **`BOUKENSHA_DIR` env var** — set this to point at any directory you like.
2. **`~/.boukensha`** — the default location for a real install.

```
.boukensha/
  .env                 # stores credentials eg. LLMs APIs (never committed to repo)
  settings.yaml        # all non-secret settings
  prompts/
    <task>/
      system.md        # per-task override for the default system prompt (optional)
```

## Run Example

```bash
./week1_baseline/bin/python/02_the_registry
```

Expected output (values from your `.boukensha/`):

```
=== Boukensha Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=... tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction (north, so params=['direction']>
  #<Tool name=shout description=Shout a message so everyone in the zone c params=['message']>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

## Considerations

These are things we observed but we do not want fixed since future steps
will build on them.

- **No string/symbol key translation in `dispatch`.** Ruby's `dispatch`
  converts the args hash's string keys to symbols
  (`args.transform_keys(&:to_sym)`) before splatting them into the block,
  because Ruby keyword arguments must be symbols while the args arrive as a
  string-keyed hash (as if parsed from JSON). This is a real gotcha in
  production harnesses, and the Ruby README calls it out explicitly. Python
  keyword arguments are always strings under the hood, so
  `tool.block(**args)` needs no translation step — the lesson the Ruby step
  teaches simply doesn't apply on the Python side. This is a natural
  divergence from a 1:1 port, not a corner cut in translation.
- **The Ruby README's sample output for this step doesn't match its own
  step's code.** It shows `#<Context turns=0 tools=2 budget=8192>`, but
  `context.rb` (unchanged from `01_struct_skeleton`) has no `budget`
  attribute and its `to_s` includes `task=...`. This looks like a leftover
  from a later, not-yet-ported step. The Python "Run Example" output above
  reflects what the ported code actually prints
  (`task=player turns=0 tools=2`, no `budget`) rather than the mismatched
  Ruby sample.
- `Config.__str__`, `Context.__str__`, `Tool.__str__`, and `Message.__str__`
  all keep the `#<...>`-style Ruby repr for parity with the Ruby port,
  rather than Python's usual `ClassName(field=value)` dataclass repr.

## Naming conventions for this port

- Ruby's `prompt_override?` is `is_prompt_override` here (not a bare
  `prompt_override`, since that name is already the settings dict key —
  keeping the `is_` prefix avoids the clash). Apply this convention to any
  future `?`-suffixed method ported from Ruby.
