# Python Port Plan — 03 · The Prompt Builder

## Goal

Port `week1_baseline/ruby/03_prompt_builder` to Python, replacing the
contents of `week1_baseline/python/03_prompt_builder`. This step adds a
`PromptBuilder` that delegates serialization of a `Context` to one of five
pluggable **backends** (`Anthropic`, `Ollama`, `OllamaCloud`, `OpenAI`,
`Gemini`), each translating the same in-memory conversation into the exact
wire format its API expects. It also adds a `Backends::Base` contract that
validates models against a static per-backend model table and exposes
cost/context-window metadata, plus a second custom error class,
`UnsupportedModelError`.

## Starting state (found during planning)

`week1_baseline/python/03_prompt_builder/` currently exists but is an
**unmodified copy of the `02_the_registry` port** — same leftover
copy-paste pattern called out in the `02_the_registry` plan:

- `README.md` is titled "02 · The Tool Registry (Python)" and documents the
  `Registry` only — no mention of `PromptBuilder` or backends.
- `examples/example.py` prints `"=== Boukensha Step 2: Tool Registry ==="`
  and never touches a backend or builds a payload.
- There is no `boukensha/prompt_builder.py`, no `boukensha/backends/`
  package, and no `prompts/system.md` under
  `week1_baseline/python/03_prompt_builder/`.
- `boukensha/errors.py` has `UnknownToolError` only —
  `UnsupportedModelError` is missing.
- `boukensha/config.py` has no `PROMPTS_DIR` constant.
- `boukensha/__init__.py` doesn't export `PromptBuilder`,
  `UnsupportedModelError`, or any backend class.
- `week1_baseline/bin/python/03_prompt_builder` **does not exist yet** —
  there's no launcher for this step at all (unlike `02`, where the
  launcher existed but pointed at the wrong directory).

One thing is *not* stale: `boukensha/tasks/base.py` and
`boukensha/tasks/player.py` already carry the full prompt-resolution logic
(`provider`, `model`, `is_prompt_override`, `prompt`, `system_prompt`,
`user_prompts_dir`/`default_prompts_dir`) needed by this step, and it's a
faithful match for the current `lib/boukensha/tasks/base.rb`. `context.py`,
`message.py`, `tool.py`, and `registry.py` are likewise already correct and
carry forward unchanged (confirmed by diffing the Ruby step's `lib/` against
`02_the_registry`'s `lib/` — only `config.rb` and `errors.rb` gained new
lines, everything else is byte-identical).

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/03_prompt_builder/README.md` | Spec/behaviour doc — backend tables, wire-format JSON samples, and Considerations are ported from here |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/prompt_builder.rb` | `Boukensha::PromptBuilder` — thin delegator to a backend |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/base.rb` | `Boukensha::Backends::Base` — model validation, cost/context-window metadata |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/anthropic.rb` | Anthropic backend — system as top-level field, tool_result wrapped in a user message |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/ollama.rb` | Ollama (local) backend — system folded into messages, `function`-wrapped tools |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/ollama_cloud.rb` | Ollama Cloud backend — same shape as Ollama plus Bearer auth |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/openai.rb` | OpenAI backend — same `function`-wrapped tools, `tool_call_id`, `max_completion_tokens` |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/backends/gemini.rb` | Gemini backend — `model` role instead of `assistant`, `functionDeclarations`/`functionResponse` |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/errors.rb` | Adds `UnsupportedModelError` alongside `UnknownToolError` |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/config.rb` | Adds `PROMPTS_DIR` constant; everything else unchanged from `02` |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/tasks/base.rb` | Unchanged from `02` (diffed — identical) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/tasks/player.rb` | Unchanged from `02` (diffed — identical) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/tool.rb` | Unchanged from `02` (diffed — identical) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/message.rb` | Unchanged from `02` (diffed — identical) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/context.rb` | Unchanged from `02` (diffed — identical, trailing-newline only) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha/registry.rb` | Unchanged from `02` (diffed — identical) |
| `week1_baseline/ruby/03_prompt_builder/lib/boukensha.rb` | Top-level require — now also requires `prompt_builder` and all five `backends/*` |
| `week1_baseline/ruby/03_prompt_builder/prompts/system.md` | Default system prompt shipped with the step |
| `week1_baseline/ruby/03_prompt_builder/examples/example.rb` | Runnable smoke-test — registers `look`/`move` tools, seeds a user/assistant/tool_result conversation, picks a backend from `settings.yaml`, and prints the pretty-printed API payload. Port line-for-line. |
| `week1_baseline/ruby/03_prompt_builder/Gemfile` / `Gemfile.lock` | Still just `dotenv` — no new dependency for this step (no HTTP calls are actually made; only payload construction) |

Also reference the already-completed `02_the_registry` port
(`week1_baseline/python/02_the_registry/`) for established Python
conventions this step continues: `is_prompt_override` naming, `#<...>`-style
`__str__` for parity, single `example.py`, shared root `.venv`, leading-
underscore private helpers (`_resolve_dir`, `_load_env`, ...).

## Design Considerations

- **New `backends/` subpackage, one module per backend** — direct 1:1
  mirror of `lib/boukensha/backends/`: `base.py`, `anthropic.py`,
  `ollama.py`, `ollama_cloud.py`, `openai.py`, `gemini.py`, plus an empty
  `__init__.py` (matching the existing empty `tasks/__init__.py`).
- **Model tables: Ruby symbol keys → plain Python string keys.** Ruby's
  `MODELS` hashes use `:context_window`, `:cost_per_million`, `:input`,
  `:output`, `:usage_unit`, `:usage_level` as symbol keys. Python has no
  symbol type, so these become ordinary string keys
  (`"context_window"`, `"cost_per_million"`, ...) — same pattern already
  used for `Tool#parameters` in `01_struct_skeleton`.
- **`model_info` name collision — Ruby's separate class/instance method
  namespaces have no Python equivalent.** `backends/base.rb` defines *two*
  different things both named `model_info`: a **class method**
  `self.model_info(model)` (table lookup) and an **instance method**
  `model_info` with no args (reader for `@model_info`). Ruby keeps these
  apart because class methods and instance methods live in separate method
  tables. Python classmethods and instance methods share one namespace on
  the class body, so defining both under the same name would silently
  clobber one. Resolution: rename the **classmethod** to
  `model_info_for(cls, model)`; keep the **instance-facing** name
  `model_info` as a `@property` reading a private `self._model_info`
  backing attribute — this preserves the Ruby *instance* API exactly
  (`backend.model_info`, `backend.context_window`, etc. all keep their
  names) and only renames the internal lookup helper that nothing outside
  `Base` calls directly.
- **`estimate_cost`'s truthiness check is a 0.0-falsy trap in Python — must
  use explicit `is None`, not a truthy check.** Ruby:
  `return nil unless input_token_cost_per_million && output_token_cost_per_million`.
  In Ruby, `0.0` is truthy (only `nil`/`false` are falsy), so this
  correctly *proceeds* to compute `0.0` for local Ollama models (whose
  costs are literally `0.0`, per the README: *"For local Ollama models,
  token API cost is `0.0`"*). A naive Python port —
  `if not (input_cost and output_cost): return None` — would incorrectly
  return `None` for those same models, because `0.0` is falsy in Python.
  The Python port must check `is None` explicitly:
  `if input_cost is None or output_cost is None: return None`. This is the
  one place in this step where a literal translation silently changes
  behavior, so it gets called out rather than fixed quietly.
- **`validate_model!` → `validate_model`.** First bang-method in the
  codebase so far; Python has no bang-method convention, so it's dropped,
  consistent with how `dispatch` and other mutating/raising methods were
  already named without decoration in `01`/`02`.
- **Message roles need no symbol→string translation — already a non-issue
  in this Python port.** Ruby backends do `msg.role.to_s` / compare against
  `:tool_result`/`:assistant` symbols. The existing Python `Message`
  dataclass already types `role: str` (established in `01_struct_skeleton`
  and unchanged since), so every backend just compares/writes `msg.role`
  directly — same "no translation step needed" situation the `02` plan
  called out for `dispatch`.
- **`Backends::Base` is intentionally *not* re-exported from the top-level
  `boukensha/__init__.py`.** `Tasks::Base` was never re-exported either
  (only `Player` is, from `02` onward) — following that precedent avoids a
  same-name collision between `boukensha.tasks.base.Base` and
  `boukensha.backends.base.Base` at the package's flat top-level namespace,
  which Ruby's real module nesting (`Boukensha::Tasks::Base` vs
  `Boukensha::Backends::Base`) never has to worry about. Only the five
  concrete backend classes (`Anthropic`, `Ollama`, `OllamaCloud`, `OpenAI`,
  `Gemini`) are re-exported, matching what `example.rb` actually
  instantiates.
- **`PromptBuilder#to_messages` / `#to_tools` inherit a latent Ruby arity
  bug — port it faithfully, don't fix it.** `prompt_builder.rb` calls
  `@backend.to_messages(@context.messages)` (one arg), but
  `Ollama`/`OllamaCloud`/`OpenAI#to_messages` are defined as
  `to_messages(system, messages)` (two args) — calling
  `builder.to_messages` against any of those three backends would raise a
  Ruby `ArgumentError`. Only `Anthropic#to_messages(messages)` and
  `Gemini#to_messages(messages)` actually match the one-arg call. This
  never surfaces because `example.rb` only ever calls
  `builder.to_api_payload`, which goes through `backend.to_payload`
  instead (which *does* call `to_messages` with the right arity
  internally). The Python port mirrors the same one-arg calls in
  `PromptBuilder.to_messages`/`.to_tools` for faithful parity — see Open
  Questions for whether to flag this back upstream.
- **`Config.PROMPTS_DIR` lands at the same real directory as Ruby's, via a
  different `.parent` depth.** Ruby: `File.expand_path("../../prompts", __dir__)`
  from `lib/boukensha/config.rb` — `__dir__` is already a directory
  (`lib/boukensha`), and two `".."` climb past `lib/` to the step root.
  Python has no `lib/` wrapper (`boukensha/config.py` sits directly under
  the step root), and `__file__` is a *file* path, not a directory, so the
  equivalent is `Path(__file__).resolve().parent.parent / "prompts"` — the
  first `.parent` strips the filename down to the `boukensha/` directory
  (Ruby's `__dir__` equivalent), the second climbs to the step root. Same
  destination (`week1_baseline/python/03_prompt_builder/prompts`), reached
  with two `.parent` calls instead of two `".."` segments because Python's
  starting point is one directory level "deeper" in path-string terms.
- **No new dependency.** Backends only build payload dicts — none of them
  perform an actual HTTP request in this step (the README says as much:
  *"PromptBuilder does not call the API"*). `requirements.txt` stays
  `PyYAML` + `python-dotenv`, unchanged from `02`.
- **Folder layout: snapshot per step, unchanged approach** — overwrite the
  existing (currently mis-copied) `python/03_prompt_builder/` in place,
  same as every prior step.

## Target file layout

```
week1_baseline/python/03_prompt_builder/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # rewritten for this step (currently copy of 02's)
  prompts/
    system.md                      # new: default system prompt
  boukensha/
    __init__.py                    # adds PromptBuilder, UnsupportedModelError, 5 backend classes
    config.py                      # adds PROMPTS_DIR constant
    tool.py                        # unchanged from 02_the_registry
    message.py                     # unchanged from 02_the_registry
    context.py                     # unchanged from 02_the_registry
    errors.py                      # adds UnsupportedModelError
    registry.py                    # unchanged from 02_the_registry
    prompt_builder.py              # new: PromptBuilder
    backends/
      __init__.py                  # new, empty (matches tasks/__init__.py)
      base.py                      # new: Backends.Base
      anthropic.py                 # new
      ollama.py                    # new
      ollama_cloud.py              # new
      openai.py                    # new
      gemini.py                    # new
    tasks/
      __init__.py                  # unchanged
      base.py                      # unchanged from 02_the_registry
      player.py                    # unchanged from 02_the_registry
  examples/
    example.py                     # rewritten for this step (currently copy of 02's)
week1_baseline/bin/python/03_prompt_builder   # new launcher (doesn't exist yet)
```

## Porting notes (Ruby → Python mapping)

### `errors.py` — add `UnsupportedModelError`

```python
class UnknownToolError(Exception):
    pass


class UnsupportedModelError(Exception):
    pass
```

### `config.py` — add `PROMPTS_DIR`

Inserted right after `DEFAULT_DIR`, matching the Ruby constant's placement:

```python
class Config:
    DEFAULT_DIR = Path.home() / ".boukensha"

    # Default prompts shipped alongside the package code.
    PROMPTS_DIR = str(Path(__file__).resolve().parent.parent / "prompts")

    ...
```

### `backends/base.py` (`backends/base.rb` → `backends/base.py`)

```ruby
class Base
  attr_reader :model

  def self.models
    const_get(:MODELS)
  rescue NameError
    raise NotImplementedError, "#{self} must define MODELS"
  end

  def self.model_info(model)
    models[model.to_s]
  end

  def self.validate_model!(model)
    model = model.to_s
    return model if model_info(model)

    supported = models.keys.sort.join(", ")
    raise UnsupportedModelError, "#{name} does not support model #{model.inspect}. Supported models: #{supported}"
  end

  def model_info
    @model_info
  end

  def context_window
    model_info.fetch(:context_window)
  end

  def input_token_cost_per_million
    model_info.fetch(:cost_per_million).fetch(:input)
  end

  def output_token_cost_per_million
    model_info.fetch(:cost_per_million).fetch(:output)
  end

  def usage_unit
    model_info.fetch(:usage_unit)
  end

  def usage_level
    model_info[:usage_level]
  end

  def estimate_cost(input_tokens:, output_tokens:)
    return nil unless input_token_cost_per_million && output_token_cost_per_million

    ((input_tokens * input_token_cost_per_million) +
      (output_tokens * output_token_cost_per_million)) / 1_000_000.0
  end

  private

  def configure_model(model)
    @model = self.class.validate_model!(model)
    @model_info = self.class.model_info(@model)
  end
end
```

```python
from ..errors import UnsupportedModelError


class Base:
    @classmethod
    def models(cls):
        models = getattr(cls, "MODELS", None)
        if models is None:
            raise NotImplementedError(f"{cls} must define MODELS")
        return models

    # Renamed from Ruby's class-level `model_info(model)` — see Design
    # Considerations for why this can't share a name with the instance
    # property below in Python.
    @classmethod
    def model_info_for(cls, model):
        return cls.models().get(str(model))

    @classmethod
    def validate_model(cls, model):
        model = str(model)
        if cls.model_info_for(model):
            return model

        supported = ", ".join(sorted(cls.models().keys()))
        raise UnsupportedModelError(
            f"{cls.__name__} does not support model {model!r}. Supported models: {supported}"
        )

    @property
    def model_info(self):
        return self._model_info

    @property
    def context_window(self):
        return self._model_info["context_window"]

    @property
    def input_token_cost_per_million(self):
        return self._model_info["cost_per_million"]["input"]

    @property
    def output_token_cost_per_million(self):
        return self._model_info["cost_per_million"]["output"]

    @property
    def usage_unit(self):
        return self._model_info["usage_unit"]

    @property
    def usage_level(self):
        return self._model_info.get("usage_level")

    def estimate_cost(self, input_tokens, output_tokens):
        input_cost = self.input_token_cost_per_million
        output_cost = self.output_token_cost_per_million
        if input_cost is None or output_cost is None:
            return None

        return ((input_tokens * input_cost) + (output_tokens * output_cost)) / 1_000_000.0

    def _configure_model(self, model):
        self.model = self.validate_model(model)
        self._model_info = self.model_info_for(self.model)
```

### `backends/anthropic.py`

```python
from .base import Base


class Anthropic(Base):
    BASE_URL = "https://api.anthropic.com/v1/messages"
    MODELS = {
        "claude-haiku-4-5": {
            "context_window": 200_000,
            "cost_per_million": {"input": 1.0, "output": 5.0},
            "usage_unit": "tokens",
        },
        "claude-haiku-4-5-20251001": {
            "context_window": 200_000,
            "cost_per_million": {"input": 1.0, "output": 5.0},
            "usage_unit": "tokens",
        },
        "claude-sonnet-4-6": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 3.0, "output": 15.0},
            "usage_unit": "tokens",
        },
        "claude-opus-4-8": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 5.0, "output": 25.0},
            "usage_unit": "tokens",
        },
    }

    def __init__(self, api_key, model):
        self.api_key = api_key
        self._configure_model(model)

    def to_messages(self, messages):
        result = []
        for msg in messages:
            if msg.role == "tool_result":
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_use_id,
                        "content": msg.content,
                    }],
                })
            else:
                result.append({"role": msg.role, "content": msg.content})
        return result

    def to_tools(self, tools):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys()),
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "system": context.system,
            "max_tokens": max_output_tokens,
            "tools": self.to_tools(context.tools),
            "messages": self.to_messages(context.messages),
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def url(self):
        return self.BASE_URL
```

### `backends/ollama.py`

Same model-table shape (all `"local_compute"` usage unit, `0.0` costs —
this is the backend that exercises the `estimate_cost` 0.0-falsy fix).
System prompt folded into the messages array; tool results use
`tool_name` keyed by `tool_use_id`.

```python
from .base import Base


class Ollama(Base):
    MODELS = {
        "gemma4": {"context_window": 128_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "gemma4:e2b": {"context_window": 128_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "gemma4:e4b": {"context_window": 128_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "gemma4:12b": {"context_window": 256_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "gemma4:26b": {"context_window": 256_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "gemma4:31b": {"context_window": 256_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "qwen3:30b": {"context_window": 256_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "qwen3:8b": {"context_window": 40_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
        "deepseek-r1:8b": {"context_window": 128_000, "cost_per_million": {"input": 0.0, "output": 0.0}, "usage_unit": "local_compute"},
    }

    def __init__(self, model, host="http://localhost:11434"):
        self.host = host
        self._configure_model(model)

    def to_messages(self, system, messages):
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                conversation.append({"role": "tool", "tool_name": msg.tool_use_id, "content": msg.content})
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_tools(self, tools):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "stream": False,
            "messages": self.to_messages(context.system, context.messages),
            "tools": self.to_tools(context.tools),
        }

    def headers(self):
        return {"Content-Type": "application/json"}

    def url(self):
        return f"{self.host}/api/chat"
```

### `backends/ollama_cloud.py`

Same `to_messages`/`to_tools`/`to_payload` shape as `Ollama`; differs in
model table (`"ollama_cloud_usage"` unit, `usage_level`, `None` costs —
`estimate_cost` returns `None` here, correctly, since these really are
unknown/`None`, not `0.0`), fixed `BASE_URL`, and Bearer auth header.

```python
from .base import Base


class OllamaCloud(Base):
    BASE_URL = "https://ollama.com"
    MODELS = {
        "gemma4:31b-cloud": {
            "context_window": 256_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "medium",
        },
        "minimax-m3:cloud": {
            "context_window": 512_000,
            "advertised_context_window": 1_000_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "high",
        },
        "kimi-k2.5:cloud": {
            "context_window": 256_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "high",
        },
    }

    def __init__(self, api_key, model):
        self.api_key = api_key
        self._configure_model(model)

    def to_messages(self, system, messages):
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                conversation.append({"role": "tool", "tool_name": msg.tool_use_id, "content": msg.content})
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_tools(self, tools):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "stream": False,
            "messages": self.to_messages(context.system, context.messages),
            "tools": self.to_tools(context.tools),
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def url(self):
        return f"{self.BASE_URL}/api/chat"
```

### `backends/openai.py`

Same `function`-wrapped tool shape as Ollama; tool results use
`tool_call_id` instead of `tool_name`; payload uses
`max_completion_tokens` instead of `max_tokens`/`stream`.

```python
from .base import Base


class OpenAI(Base):
    BASE_URL = "https://api.openai.com/v1/chat/completions"
    MODELS = {
        "gpt-5.5": {"context_window": 1_000_000, "cost_per_million": {"input": 5.0, "output": 30.0}, "usage_unit": "tokens"},
        "gpt-5.4": {"context_window": 1_000_000, "cost_per_million": {"input": 2.5, "output": 15.0}, "usage_unit": "tokens"},
        "gpt-5.4-mini": {"context_window": 400_000, "cost_per_million": {"input": 0.75, "output": 4.5}, "usage_unit": "tokens"},
    }

    def __init__(self, api_key, model):
        self.api_key = api_key
        self._configure_model(model)

    def to_messages(self, system, messages):
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                conversation.append({"role": "tool", "tool_call_id": msg.tool_use_id, "content": msg.content})
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_tools(self, tools):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                },
            }
            for tool in tools.values()
        ]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "model": self.model,
            "messages": self.to_messages(context.system, context.messages),
            "tools": self.to_tools(context.tools),
            "max_completion_tokens": max_output_tokens,
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def url(self):
        return self.BASE_URL
```

### `backends/gemini.py`

The one backend with real shape differences: `assistant` → `model` role,
`parts`/`text` wrapping, `functionDeclarations`/`functionResponse`, system
sent as a top-level `systemInstruction` (so `to_messages` here takes
`messages` only, matching `PromptBuilder`'s one-arg call exactly — see
Design Considerations).

```python
from .base import Base


class Gemini(Base):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODELS = {
        "gemini-3.5-flash": {"context_window": 1_048_576, "cost_per_million": {"input": 1.5, "output": 9.0}, "usage_unit": "tokens"},
        "gemini-3.1-flash-lite": {"context_window": 1_048_576, "cost_per_million": {"input": 0.25, "output": 1.5}, "usage_unit": "tokens"},
        "gemini-2.5-pro": {"context_window": 1_048_576, "cost_per_million": {"input": 1.25, "output": 10.0}, "usage_unit": "tokens"},
        "gemini-2.5-flash": {"context_window": 1_048_576, "cost_per_million": {"input": 0.30, "output": 2.50}, "usage_unit": "tokens"},
        "gemini-2.5-flash-lite": {"context_window": 1_048_576, "cost_per_million": {"input": 0.10, "output": 0.40}, "usage_unit": "tokens"},
    }

    def __init__(self, api_key, model):
        self.api_key = api_key
        self._configure_model(model)

    def to_messages(self, messages):
        result = []
        for msg in messages:
            if msg.role == "assistant":
                result.append({"role": "model", "parts": [{"text": msg.content}]})
            elif msg.role == "tool_result":
                result.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.tool_use_id,
                            "response": {"content": msg.content},
                        }
                    }],
                })
            else:
                result.append({"role": msg.role, "parts": [{"text": msg.content}]})
        return result

    def to_tools(self, tools):
        if not tools:
            return []

        return [{
            "functionDeclarations": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys()),
                    },
                }
                for tool in tools.values()
            ]
        }]

    def to_payload(self, context, max_output_tokens=1024):
        return {
            "systemInstruction": {"parts": [{"text": context.system}]},
            "contents": self.to_messages(context.messages),
            "tools": self.to_tools(context.tools),
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        }

    def headers(self):
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

    def url(self):
        return f"{self.BASE_URL}/{self.model}:generateContent"
```

### `prompt_builder.py` (`prompt_builder.rb` → `prompt_builder.py`)

```python
class PromptBuilder:
    def __init__(self, context, backend):
        self.context = context
        self.backend = backend

    def to_messages(self):
        return self.backend.to_messages(self.context.messages)

    def to_tools(self):
        return self.backend.to_tools(self.context.tools)

    def to_api_payload(self, max_output_tokens=1024):
        return self.backend.to_payload(self.context, max_output_tokens=max_output_tokens)

    def headers(self):
        return self.backend.headers()

    def url(self):
        return self.backend.url()
```

### `prompts/system.md`

Copied verbatim:

```
You are a MUD player assistant. Use the tools available to you to help the player explore, fight, and interact with the world.
```

### `boukensha/__init__.py`

Mirrors the expanded `lib/boukensha.rb`, which now also requires
`prompt_builder` and all five `backends/*`. `Backends::Base` is
deliberately not re-exported (see Design Considerations):

```python
from .backends.anthropic import Anthropic
from .backends.gemini import Gemini
from .backends.ollama import Ollama
from .backends.ollama_cloud import OllamaCloud
from .backends.openai import OpenAI
from .config import Config
from .context import Context
from .errors import UnknownToolError, UnsupportedModelError
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

__all__ = [
    "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI",
    "Config", "Context", "UnknownToolError", "UnsupportedModelError",
    "Message", "PromptBuilder", "Registry", "Player", "Tool",
]
```

### Example (`example.rb` → `examples/example.py`)

Port every `puts` line 1:1, including the provider `case`/`when` → Python
`if`/`elif` chain and the `ENV.fetch(...)` calls → plain `os.environ[...]`
subscripting (both raise on a missing key with no default supplied — no
custom helper needed):

```python
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boukensha import (
    Anthropic,
    Config,
    Context,
    Gemini,
    Ollama,
    OllamaCloud,
    OpenAI,
    Player,
    PromptBuilder,
    Registry,
)

os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR,
)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

registry.tool(
    "look",
    description="Look around the current room for details",
    parameters={},
    block=lambda: "A damp stone corridor stretches north. Torches flicker on the walls.",
)

registry.tool(
    "move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string", "description": "The direction to move"}},
    block=lambda direction: f"You move {direction} into a torch-lit corridor.",
)

ctx.add_message("user", "I just arrived in the dungeon. What's around me, and can you move north?")
ctx.add_message("assistant", "Let me take a look around first.")
ctx.add_message(
    "tool_result",
    "A damp stone corridor stretches north. Torches flicker on the walls.",
    tool_use_id="toolu_01X",
)

print("=== BOUKENSHA Step 3: Prompt Builder ===")
provider = Player.provider(player_settings)
model = Player.model(player_settings)

if provider == "anthropic":
    backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model=model)
elif provider == "ollama":
    backend = Ollama(model=model)
elif provider == "ollama_cloud":
    backend = OllamaCloud(api_key=os.environ["OLLAMA_API_KEY"], model=model)
elif provider == "openai":
    backend = OpenAI(api_key=os.environ["OPENAI_API_KEY"], model=model)
elif provider == "gemini":
    backend = Gemini(api_key=os.environ["GEMINI_API_KEY"], model=model)
else:
    raise ValueError(f"Unsupported provider for player task: {provider}")

builder = PromptBuilder(ctx, backend)

print()
print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print(json.dumps(builder.to_api_payload(), indent=2))
```

Notes on the non-mechanical lines:

- `JSON.pretty_generate(builder.to_api_payload)` → `json.dumps(..., indent=2)`.
  Exact whitespace/formatting will differ slightly between Ruby's and
  Python's pretty-printers (this is expected, not a bug); the payload
  *structure* and key ordering are what must match, and both are preserved
  since Python dicts keep insertion order.
- Ruby's `registry.tool("look", ...) do ... end` takes a block with no
  parameters; the Python equivalent is a zero-arg `lambda:` block, same
  pattern already established for `"shout"` in `02`.

### `README.md`

Rewritten for this step, following the Python README structure established
in `01`/`02` (Setup / ... / Considerations / Run Example), replacing the
Registry-focused body with:

- The same overview paragraph and "How It Works" diagram from the Ruby
  README (fixing the two source typos — "cosntantly" → "constantly",
  "serveral" → "several" — since this is prose being carried forward, not
  ported code).
- A `Boukensha.PromptBuilder` method table (`to_messages`, `to_tools`,
  `to_api_payload`, `headers`, `url`).
- The **Backends** section: the shared model-metadata table
  (`context_window`, `cost_per_million.input`/`.output`, `usage_unit`,
  `usage_level`), backend instance properties, and one subsection per
  backend with its URL and required env var — content is data-format-only
  and carries over unchanged.
- The `System Prompt` / `Tool Results` / `Tool Definitions` / `Message
  Roles` JSON comparison tables verbatim — these describe wire formats, not
  Ruby syntax, so nothing needs translating.
- **Considerations**, carrying the three existing bullets forward, plus one
  new Python-specific bullet documenting the `estimate_cost` 0.0-vs-`None`
  truthiness trap called out above — worth teaching explicitly since it's
  exactly the kind of subtle cross-language bug this whole porting series
  is meant to surface.
- Updated **Run Example** pointing at
  `./week1_baseline/bin/python/03_prompt_builder`.
- The closing **Note for Future** paragraph, unchanged.

### Launcher (`bin/python/03_prompt_builder`, new)

Doesn't exist yet (unlike `02`, where it existed but pointed at the wrong
step). Create following the established fixed pattern:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
cd "$SCRIPT_DIR/../../python/03_prompt_builder"
"$REPO_ROOT/.venv/bin/python" examples/example.py
```

Needs `chmod +x` after creation, matching the other launchers.

## Cleanup

- Delete any stray `__pycache__/` directories currently sitting in
  `python/03_prompt_builder/` (leftover from running the stale `02`-copy) —
  confirmed present under `boukensha/__pycache__/` and
  `boukensha/tasks/__pycache__/`.

## Configuration Schema

Unchanged in shape — this step still reads `tasks.player.provider` and
`tasks.player.model` from `settings.yaml` (already required by `Tasks::Base`
since `02`), plus the pre-existing `prompt_override` block. No new keys are
introduced by this step's Ruby source; whichever provider/model the current
`~/.boukensha/settings.yaml` (or `.boukensha/settings.yaml` in-repo, per
`BOUKENSHA_DIR`) already specifies for `tasks.player` will be exercised by
the ported example, same as it is by the Ruby one. Same schema as
documented in the `00_config` plan.

## Open Questions

1. **Faithfully port the `PromptBuilder#to_messages`/`#to_tools` arity bug,
   or fix it during the port?** As detailed in Design Considerations, the
   Ruby `PromptBuilder#to_messages`/`#to_tools` convenience methods only
   work correctly against the `Anthropic` and `Gemini` backends — calling
   them against `Ollama`, `OllamaCloud`, or `OpenAI` would raise (wrong
   arity). This is never exercised by `example.rb`, which only calls
   `to_api_payload`. Recommendation: port it faithfully (mirrors the
   reference source 1:1, and the divergence is invisible to the example),
   and just leave the note in Design Considerations rather than silently
   "fixing" behavior the Ruby step doesn't actually exercise or document as
   a known limitation. Confirm before implementation — this is the one
   spot where "faithful port" and "correct code" pull in different
   directions.
2. **Which provider will the example actually exercise?** `example.rb`/
   `example.py` both branch on `tasks.player.provider` from
   `settings.yaml` at runtime. Whichever backend that resolves to in the
   local `.boukensha/settings.yaml` needs its corresponding API key env var
   set (`ANTHROPIC_API_KEY`, `OLLAMA_API_KEY`, `OPENAI_API_KEY`, or
   `GEMINI_API_KEY`) — Ollama alone needs no key but does need `ollama
   serve` running locally. Given the "Note for Future" in the README says
   *"we will only use Claude for now"*, `anthropic` is the expected
   provider, so `ANTHROPIC_API_KEY` should already be set from the key you
   just added — but this is worth confirming against the actual
   `settings.yaml` content before running the ported example, since a
   missing env var will raise `KeyError` (matching Ruby's `ENV.fetch`
   behavior) rather than silently falling back.
