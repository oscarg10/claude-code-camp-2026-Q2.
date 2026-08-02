# Python Port Plan — 05 · The Agent Loop

## Goal

Port `week1_baseline/ruby/05_agent_loop` to Python, creating
`week1_baseline/python/05_agent_loop` from scratch. This step adds
`Boukensha::Agent` — the actual agent loop: send a request, check whether
the model wants to call a tool, dispatch it via `Registry`, feed the result
back, repeat, until the model signals `stop_reason: "end_turn"` or an
iteration ceiling triggers a short tools-disabled wind-down call instead.
To make that loop provider-agnostic, every backend gains a `parse_response`
method that normalizes its raw wire response into one common
`{stop_reason, content}` shape, plus the inverse (`assistant_message`/
`assistant_parts`) for replaying an assistant turn with tool calls back
into that provider's format on the next request.

## Starting state (found during planning)

Unlike every prior step, **`week1_baseline/python/05_agent_loop/` doesn't
exist at all yet** — there's no stale copy to fix, just an empty slot.
`week1_baseline/bin/python/05_agent_loop` doesn't exist either.
`week1_baseline/bin/ruby/05_agent_loop` already exists and is correct (the
launcher pattern, not its target — nothing to fix there).

This plan builds the step directly from `04_api_client`'s already-correct
Python port plus this step's additions, rather than describing a
stale-copy cleanup.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/05_agent_loop/README.md` | Spec/behaviour doc — `Agent` method table, normalized response shape, task config table, and Considerations are ported from here |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/agent.rb` | `Boukensha::Agent` — the loop itself: `run`, iteration/wind-down resolution, tool-call dispatch |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/errors.rb` | Adds `LoopError` — **declared but never raised anywhere in this step**, see Design Considerations |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/tasks/base.rb` | Adds `DEFAULT_MAX_ITERATIONS`/`DEFAULT_MAX_OUTPUT_TOKENS`, `max_iterations(settings)`, `max_output_tokens(settings)`, private `integer_setting` |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/client.rb` | `call` gains a `tools:` keyword, threaded through to `to_api_payload` |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/prompt_builder.rb` | `to_api_payload` threads `tools:` through; adds `parse_response`, delegating to the backend |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/backends/anthropic.rb` | `to_payload` gains `tools:` override param; adds `parse_response` |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/backends/ollama.rb` | `to_payload` gains `tools:`; adds `parse_response` + private `assistant_message`; `to_messages` gains an `:assistant` branch |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/backends/ollama_cloud.rb` | Same shape as `ollama.rb` — duplicated, not shared |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/backends/openai.rb` | Same shape, plus real tool-call `id`s and JSON-string `arguments` (needs `require "json"`) |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/backends/gemini.rb` | Same shape, `parse_response` reads `candidates[0].content.parts`; private `assistant_parts` (not `assistant_message` — different name, same role) |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha.rb` | Top-level require — now also requires `agent` |
| `week1_baseline/ruby/05_agent_loop/examples/example.rb` | Runnable smoke-test — registers `read_file`/`list_directory` anchored to the step directory (not CWD), seeds one real user message, builds `Agent`, runs it, prints the final response. Port line-for-line. |
| `week1_baseline/ruby/05_agent_loop/lib/boukensha/tool.rb`, `message.rb`, `context.rb`, `registry.rb`, `config.rb`, `backends/base.rb`, `tasks/player.rb` | Unchanged from `04_api_client` (diffed — identical or cosmetic-only, see below) |
| `week1_baseline/ruby/05_agent_loop/Gemfile` / `Gemfile.lock` | Still just `dotenv` — `Agent` adds no dependency |

Also reference the already-completed `04_api_client` port
(`week1_baseline/python/04_api_client/`) — this step's Python source
directory is built starting from a copy of that one's `boukensha/`,
`prompts/`, and `requirements.txt`.

## Design Considerations

- **Whole new step directory, not a stale-copy fix.** Every prior plan's
  "Starting state" section described undoing leftover copy-paste from the
  previous step. This one doesn't apply — there's nothing to fix, only
  files to create, seeded from `04`'s already-correct content.
- **`config.py` and `context.py` need zero changes — port them forward
  byte-identical.** Ruby's `config.rb` diff from `04`→`05` is purely
  Ruby-syntax cosmetics (`def mud_host = dig(:mud, :host) || "localhost"`
  one-liner "endless method" syntax replacing the equivalent multi-line
  `def...end` — same behavior, Ruby 3.0+ style choice). `context.rb` has
  **no diff at all**. The Ruby README's own "Updated Files" table claims
  *"`lib/boukensha/context.rb` | Carries the active task object alongside
  messages and tools"* — but `Context` has carried `task` since `03`. This
  is the same kind of stale/leftover documentation this whole series keeps
  finding (matching `02`'s mismatched sample output and `04`'s buggy
  `PROMPTS_DIR`) — noted here rather than silently reproduced or "fixed"
  in a way that implies new work happened.
- **`LoopError` is declared but never raised — port it as dead code, don't
  invent a use for it.** The Ruby README says *"Added `LoopError` for
  runaway agents,"* and `errors.rb` does add the class. But `Agent#run`'s
  actual max-iteration handling — `iteration_limit_reached?` → `wrap_up` —
  never raises it; the whole design explicitly treats the limit as *"a
  trigger threshold, not a hard cap"* (the class's own comment) and always
  returns a normal string, never an exception. Porting `LoopError` as an
  unused class matches the reference exactly; see Open Questions.
- **The `tools:` sentinel has three distinct states that must survive the
  port exactly: `None` (omitted), `[]` (explicitly empty), and a non-empty
  list.** This is the mechanism `wrap_up` uses to disable tools for the
  wind-down call. Every layer (`Client#call` → `PromptBuilder#to_api_payload`
  → each backend's `to_payload`) does `tools.nil? ? to_tools(context.tools)
  : tools` — i.e. *only* re-derive from `context.tools` when `tools` is
  the Ruby `nil`/Python `None` sentinel; an explicitly-passed `[]` must
  pass through untouched. The Python port uses
  `tools if tools is not None else self.to_tools(context.tools)`
  everywhere this pattern appears — a truthy check (`tools or
  self.to_tools(...)`) would be wrong here, because `[]` is falsy in
  Python and would silently get replaced with the full tool list, defeating
  the entire purpose of the wind-down call (which exists specifically to
  stop the model from calling more tools once the iteration ceiling hits).
- **`parse_response`/`assistant_message` are duplicated across
  `Ollama`/`OllamaCloud` in Ruby, not shared — the Python port keeps that
  duplication.** Both backends' implementations are byte-identical in
  Ruby, and neither factors it into `Base` or a shared module. Consistent
  with this whole series' "thin 1:1 port, no abstraction the reference
  doesn't have" stance, the Python port writes the same logic twice rather
  than introducing a mixin the Ruby source doesn't have.
- **Tool-call IDs aren't universal.** Anthropic and OpenAI assign every
  tool call a real unique `id`. Ollama, OllamaCloud, and Gemini don't —
  those three backends' `parse_response` reuse the tool's `name` as its
  `id` (and match `tool_result`s back to a call by that same name). This is
  a genuine cross-provider API-shape difference being preserved faithfully,
  not a porting shortcut — worth a one-line callout in the Python README so
  it doesn't read as a bug when someone diffs Anthropic vs. Ollama
  `tool_use` blocks side by side.
- **`Agent._call_opts`/`_wrap_up`'s truthiness gets the same `is not None`
  discipline as `estimate_cost` in `03`, for consistency — not because
  it's a live bug here.** Ruby's `@max_output_tokens ? {...} : {}` is a
  truthy check; it happens to be safe in practice because nobody
  configures `max_output_tokens: 0` (unlike `03`'s `estimate_cost`, where
  `0.0` is a real, common value for local Ollama models). Still, the
  Python port uses `if self.max_output_tokens is not None` rather than a
  bare truthy check, matching the established project-wide discipline
  around `None` vs. falsy-but-valid numeric values.
- **`base_dir`-anchored tool paths are new in this step — not a
  continuation of `04`'s CWD-relative paths.** `04`'s `read_file`/
  `list_directory` blocks resolved paths against the process's current
  working directory (`Path(path).read_text()`, no anchor). `05`'s Ruby
  blocks explicitly anchor every path to the step's own directory
  (`base_dir = File.expand_path("..", __dir__)`, then
  `File.expand_path(path, base_dir)` in each tool), so the agent reliably
  finds `05_agent_loop/README.md`, `lib/`, etc. regardless of where the
  launcher script was invoked from. Ported as
  `BASE_DIR = Path(__file__).resolve().parent.parent` in `example.py`, with
  each tool block resolving against it via `Path(BASE_DIR, path)`.
- **`list_directory`'s join separator changed from `04`'s `"\n"` to `05`'s
  `", "`** — confirmed by re-reading the Ruby source rather than assuming
  it carried over from `04`. Likely because the result now gets echoed
  inline in the `"  tool result → ..."` console line, where a
  comma-separated list reads better on one line than embedded newlines.
- **`Agent`'s Python constructor stays positional-or-keyword, not forced
  keyword-only**, consistent with every class ported in this series so far
  (`Tool`, `Context`, `Registry`, `Client`, ...), even though Ruby's
  `initialize(context:, registry:, builder:, client:, ...)` requires
  keyword arguments syntactically.
- **`Base.integer_setting`'s `Integer(value)` → Python's `int(value)`.**
  Both coerce a string or numeric setting into an integer and raise
  (`ArgumentError`/`TypeError` in Ruby, `ValueError`/`TypeError` in Python)
  on something unparseable (e.g. a settings.yaml typo like
  `max_iterations: "abc"`) — same "let it raise, don't silently coerce to
  a fallback" behavior on both sides, no special handling needed.

## Target file layout

```
week1_baseline/python/05_agent_loop/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # new
  prompts/
    system.md                      # unchanged from 04_api_client
  boukensha/
    __init__.py                    # adds Agent, LoopError
    config.py                      # unchanged from 04_api_client
    tool.py                        # unchanged from 04_api_client
    message.py                     # unchanged from 04_api_client
    context.py                     # unchanged from 04_api_client
    errors.py                      # adds LoopError
    registry.py                    # unchanged from 04_api_client
    prompt_builder.py              # updated: tools passthrough, parse_response
    client.py                      # updated: tools passthrough on call()
    agent.py                       # new: Agent
    backends/
      __init__.py                  # unchanged
      base.py                      # unchanged from 04_api_client
      anthropic.py                 # updated: tools override, parse_response
      ollama.py                    # updated: tools override, parse_response, _assistant_message
      ollama_cloud.py              # updated: tools override, parse_response, _assistant_message
      openai.py                    # updated: tools override, parse_response, _assistant_message
      gemini.py                    # updated: tools override, parse_response, _assistant_parts
    tasks/
      __init__.py                  # unchanged
      base.py                      # updated: max_iterations, max_output_tokens, _integer_setting
      player.py                    # unchanged from 04_api_client
  examples/
    example.py                     # new
week1_baseline/bin/python/05_agent_loop   # new launcher (doesn't exist yet)
```

## Porting notes (Ruby → Python mapping)

### `errors.py` — add `LoopError`

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

### `tasks/base.py` — iteration/output-token settings

```python
class Base:
    DEFAULT_MAX_ITERATIONS = 25
    DEFAULT_MAX_OUTPUT_TOKENS = 1024

    ...

    @classmethod
    def max_iterations(cls, settings):
        return cls._integer_setting(settings, "max_iterations", cls.DEFAULT_MAX_ITERATIONS)

    @classmethod
    def max_output_tokens(cls, settings):
        return cls._integer_setting(settings, "max_output_tokens", cls.DEFAULT_MAX_OUTPUT_TOKENS)

    ...

    @classmethod
    def _integer_setting(cls, settings, key, default):
        value = cls._fetch(settings, key)
        if value is None:
            return default
        return int(value)
```

(`_fetch`'s `isinstance(settings, dict)` guard from `04` is untouched;
`is_prompt_override`, `prompt`, `system_prompt`, `_read_user_prompt`,
`_read_default_prompt`, `_read_file` are untouched.)

### `client.py` — thread `tools` through `call`

```python
def call(self, max_output_tokens=1024, tools=None):
    payload = json.dumps(
        self.builder.to_api_payload(max_output_tokens=max_output_tokens, tools=tools)
    ).encode("utf-8")
    ...
```

(Rest of `Client` — retry loop, `TRANSIENT_ERRORS`, `_retryable_response`,
`_retry_delay` — unchanged from `04`.)

### `prompt_builder.py` — thread `tools`, add `parse_response`

```python
class PromptBuilder:
    def __init__(self, context, backend):
        self.context = context
        self.backend = backend

    def to_messages(self):
        return self.backend.to_messages(self.context.messages)

    def to_tools(self):
        return self.backend.to_tools(self.context.tools)

    def to_api_payload(self, max_output_tokens=1024, tools=None):
        return self.backend.to_payload(self.context, max_output_tokens=max_output_tokens, tools=tools)

    def parse_response(self, response):
        return self.backend.parse_response(response)

    def headers(self):
        return self.backend.headers()

    def url(self):
        return self.backend.url()
```

### `backends/anthropic.py` — `tools` override + `parse_response`

```python
def to_payload(self, context, max_output_tokens=1024, tools=None):
    return {
        "model": self.model,
        "system": context.system,
        "max_tokens": max_output_tokens,
        "tools": tools if tools is not None else self.to_tools(context.tools),
        "messages": self.to_messages(context.messages),
    }

def parse_response(self, response):
    stop_reason = "tool_use" if response.get("stop_reason") == "tool_use" else "end_turn"
    return {"stop_reason": stop_reason, "content": response.get("content") or []}
```

(`to_messages`, `to_tools`, `headers`, `url`, `__init__`, `MODELS`
unchanged from `04`.)

### `backends/ollama.py` — `tools` override, `parse_response`, `_assistant_message`

```python
def to_messages(self, system, messages):
    system_message = [{"role": "system", "content": system}]
    conversation = []
    for msg in messages:
        if msg.role == "tool_result":
            conversation.append({"role": "tool", "tool_name": msg.tool_use_id, "content": msg.content})
        elif msg.role == "assistant":
            conversation.append(self._assistant_message(msg.content))
        else:
            conversation.append({"role": msg.role, "content": msg.content})
    return system_message + conversation

def to_payload(self, context, max_output_tokens=1024, tools=None):
    return {
        "model": self.model,
        "stream": False,
        "messages": self.to_messages(context.system, context.messages),
        "tools": tools if tools is not None else self.to_tools(context.tools),
    }

def parse_response(self, response):
    message = response.get("message") or {}
    tool_calls = message.get("tool_calls") or []

    content = []
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})

    for tc in tool_calls:
        fn = tc.get("function") or {}
        content.append({
            "type": "tool_use",
            "id": fn.get("name"),
            "name": fn.get("name"),
            "input": fn.get("arguments") or {},
        })

    return {"stop_reason": "end_turn" if not tool_calls else "tool_use", "content": content}

def _assistant_message(self, content):
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content

    text_blocks = [b for b in blocks if b.get("type") == "text"]
    tool_blocks = [b for b in blocks if b.get("type") == "tool_use"]

    message = {"role": "assistant", "content": "".join(b["text"] for b in text_blocks)}
    if tool_blocks:
        message["tool_calls"] = [
            {"function": {"name": b["name"], "arguments": b["input"]}}
            for b in tool_blocks
        ]
    return message
```

(`to_tools`, `headers`, `url`, `__init__`, `MODELS` unchanged from `04`.)

### `backends/ollama_cloud.py`

Identical shape to `ollama.py` above (`to_messages` gains the `:assistant`
branch calling `self._assistant_message`, `to_payload` gains `tools`,
`parse_response`/`_assistant_message` are the same body) — differs only in
`BASE_URL`, `MODELS`, and Bearer auth `headers`, same as it did in `04`.

### `backends/openai.py` — real tool-call `id`s, JSON-string `arguments`

```python
import json

from .base import Base


class OpenAI(Base):
    ...

    def to_messages(self, system, messages):
        system_message = [{"role": "system", "content": system}]
        conversation = []
        for msg in messages:
            if msg.role == "tool_result":
                conversation.append({"role": "tool", "tool_call_id": msg.tool_use_id, "content": msg.content})
            elif msg.role == "assistant":
                conversation.append(self._assistant_message(msg.content))
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system_message + conversation

    def to_payload(self, context, max_output_tokens=1024, tools=None):
        return {
            "model": self.model,
            "messages": self.to_messages(context.system, context.messages),
            "tools": tools if tools is not None else self.to_tools(context.tools),
            "max_completion_tokens": max_output_tokens,
        }

    def parse_response(self, response):
        choices = response.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        tool_calls = message.get("tool_calls") or []

        content = []
        if message.get("content"):
            content.append({"type": "text", "text": message["content"]})

        for tc in tool_calls:
            function = tc.get("function") or {}
            content.append({
                "type": "tool_use",
                "id": tc.get("id"),
                "name": function.get("name"),
                "input": json.loads(function.get("arguments") or "{}"),
            })

        return {"stop_reason": "end_turn" if not tool_calls else "tool_use", "content": content}

    def _assistant_message(self, content):
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content

        text_blocks = [b for b in blocks if b.get("type") == "text"]
        tool_blocks = [b for b in blocks if b.get("type") == "tool_use"]

        message = {"role": "assistant", "content": "".join(b["text"] for b in text_blocks)}
        if tool_blocks:
            message["tool_calls"] = [
                {
                    "id": b["id"],
                    "type": "function",
                    "function": {"name": b["name"], "arguments": json.dumps(b["input"])},
                }
                for b in tool_blocks
            ]
        return message
```

(`to_tools`, `headers`, `url`, `__init__`, `MODELS` unchanged from `04`.)

### `backends/gemini.py` — `parse_response` + `_assistant_parts`

```python
def to_messages(self, messages):
    result = []
    for msg in messages:
        if msg.role == "assistant":
            result.append({"role": "model", "parts": self._assistant_parts(msg.content)})
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

def to_payload(self, context, max_output_tokens=1024, tools=None):
    return {
        "systemInstruction": {"parts": [{"text": context.system}]},
        "contents": self.to_messages(context.messages),
        "tools": tools if tools is not None else self.to_tools(context.tools),
        "generationConfig": {"maxOutputTokens": max_output_tokens},
    }

def parse_response(self, response):
    candidates = response.get("candidates") or []
    parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []

    content = []
    tool_used = False

    for part in parts:
        if part.get("functionCall"):
            fc = part["functionCall"]
            content.append({
                "type": "tool_use",
                "id": fc.get("name"),
                "name": fc.get("name"),
                "input": fc.get("args") or {},
            })
            tool_used = True
        elif part.get("text"):
            content.append({"type": "text", "text": part["text"]})

    return {"stop_reason": "tool_use" if tool_used else "end_turn", "content": content}

def _assistant_parts(self, content):
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
    parts = []
    for b in blocks:
        if b.get("type") == "tool_use":
            parts.append({"functionCall": {"name": b["name"], "args": b["input"]}})
        else:
            parts.append({"text": b["text"]})
    return parts
```

(`to_tools`, `headers`, `url`, `__init__`, `MODELS` unchanged from `04`.)

### `agent.py` (`agent.rb` → `agent.py`) — the loop

```python
from .errors import ApiError


class Agent:
    MAX_ITERATIONS = 25
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = (
        "You have reached your action limit for this turn. Do not call any more tools.\n"
        "Briefly summarize what you accomplished, what is still unfinished, and the\n"
        "single next action you would take."
    )

    def __init__(self, context, registry, builder, client,
                 task_settings=None, max_iterations=None, max_output_tokens=None):
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
        self.max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
        self.iteration = 0

    def run(self):
        while True:
            if self._iteration_limit_reached():
                return self._wrap_up("max_iterations")

            self.iteration += 1
            print(f"[iteration {self.iteration}/{self.max_iterations}]")

            response = self.client.call(**self._call_opts())
            parsed = self.builder.parse_response(response)

            if parsed["stop_reason"] == "tool_use":
                self._handle_tool_calls(parsed["content"])
            else:
                return self._extract_text(parsed["content"])

    def _resolve_max_iterations(self, task_settings, explicit):
        if explicit is not None:
            return int(explicit)
        if task_settings and hasattr(self.context.task, "max_iterations"):
            return self.context.task.max_iterations(task_settings)
        return self.MAX_ITERATIONS

    def _resolve_max_output_tokens(self, task_settings, explicit):
        if explicit is not None:
            return explicit
        if task_settings and hasattr(self.context.task, "max_output_tokens"):
            return self.context.task.max_output_tokens(task_settings)
        return None

    def _iteration_limit_reached(self):
        return self.max_iterations > 0 and self.iteration >= self.max_iterations

    def _call_opts(self):
        if self.max_output_tokens is not None:
            return {"max_output_tokens": self.max_output_tokens}
        return {}

    def _wrap_up(self, reason):
        try:
            self.context.add_message("user", self.WRAP_UP_DIRECTIVE)
            response = self.client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
            text = self._extract_text(self.builder.parse_response(response)["content"])
            return text if text.strip() else self._fallback_message(reason)
        except ApiError:
            return self._fallback_message(reason)

    def _fallback_message(self, reason):
        return (
            f"I reached my {self.max_iterations}-action limit for this turn before finishing "
            f"({reason}). Ask me to continue and I'll pick up from here."
        )

    def _extract_text(self, content):
        return "".join(b["text"] for b in content if b.get("type") == "text")

    def _handle_tool_calls(self, content):
        self.context.add_message("assistant", content)

        for block in content:
            if block.get("type") != "tool_use":
                continue

            name = block["name"]
            args = block["input"]
            use_id = block["id"]

            print(f"  tool call → {name}({args})")
            result = self.registry.dispatch(name, args)
            print(f"  tool result → {str(result)[:61]}")

            self.context.add_message("tool_result", str(result), tool_use_id=use_id)
```

Notes on the non-mechanical lines:

- `content.select { |b| b["type"] == "text" }.map { |b| b["text"] }.join` →
  `"".join(b["text"] for b in content if b.get("type") == "text")` — a
  generator expression replaces select+map+join, same result.
- `result.to_s[0..60]` (Ruby inclusive range, 61 characters) →
  `str(result)[:61]` (Python exclusive slice bound, also 61 characters) —
  double-checked these actually match rather than assuming `[0..60]` maps
  to `[:60]`.
- Ruby's `puts "  tool call → #{name}(#{args})"` interpolates a Hash,
  producing Ruby's `{"path"=>"."}` repr; the Python f-string interpolating
  a `dict` produces `{'path': '.'}` — an unavoidable language-repr
  difference in the console log line only, not the actual payload sent
  anywhere, same category as the `JSON.pretty_generate` vs. `json.dumps`
  formatting difference already noted in `03`.
- `rescue ApiError` at Ruby method scope (covering the whole `wrap_up`
  body) is ported as a `try/except` wrapping the whole `_wrap_up` body,
  not narrowed to just the `client.call` line — matching Ruby's actual
  rescue scope exactly, even though in practice only that one call can
  raise `ApiError`.

### `boukensha/__init__.py`

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
from .errors import ApiError, LoopError, UnknownToolError, UnsupportedModelError
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

__all__ = [
    "Agent", "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "LoopError", "UnknownToolError", "UnsupportedModelError",
    "Message", "PromptBuilder", "Registry", "Player", "Tool",
]
```

### Example (`example.rb` → `examples/example.py`)

```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boukensha import (
    Agent,
    Anthropic,
    Client,
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
BASE_DIR = Path(__file__).resolve().parent.parent

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

provider = Player.provider(player_settings)
model = Player.model(player_settings)

if provider == "anthropic":
    backend = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], model=model)
elif provider == "openai":
    backend = OpenAI(api_key=os.environ["OPENAI_API_KEY"], model=model)
elif provider == "gemini":
    backend = Gemini(api_key=os.environ["GEMINI_API_KEY"], model=model)
elif provider == "ollama":
    backend = Ollama(model=model)
elif provider == "ollama_cloud":
    backend = OllamaCloud(api_key=os.environ["OLLAMA_API_KEY"], model=model)
else:
    raise ValueError(f"Unsupported provider for player task: {provider}")

builder = PromptBuilder(ctx, backend)
client = Client(builder)
agent = Agent(
    context=ctx,
    registry=registry,
    builder=builder,
    client=client,
    task_settings=player_settings,
)

registry.tool(
    "read_file",
    description="Read the contents of a file from disk",
    parameters={"path": {"type": "string", "description": "The file path to read"}},
    block=lambda path: Path(BASE_DIR, path).read_text(),
)

registry.tool(
    "list_directory",
    description="List the files in a directory",
    parameters={"path": {"type": "string", "description": "The directory path to list"}},
    block=lambda path: ", ".join(
        entry for entry in os.listdir(Path(BASE_DIR, path)) if not entry.startswith(".")
    ),
)

ctx.add_message("user", "Read the README.md file and summarise what this MUD player assistant framework can do.")

print("=== BOUKENSHA Step 5: Agent Loop ===")
print()
print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print(f"Max iterations: {Player.max_iterations(player_settings)}")
print(f"Max output tokens: {Player.max_output_tokens(player_settings)}")
print()

result = agent.run()

print()
print("=== FINAL RESPONSE ===")
print(result)
```

Note the tool registration order matches Ruby exactly: `Agent` is
constructed *before* `registry.tool(...)` is called for either tool —
`registry` was already passed into `Agent`'s constructor, and `Agent`
reads `@registry`/`self.registry` lazily (only when `dispatch` actually
runs inside `_handle_tool_calls`), so tools registered afterward are still
visible. This looks backwards at first read but is exactly how the Ruby
source orders it.

### `README.md`

New file (no stale copy to rewrite), following the Python README structure
established in `01`-`04`:

- Overview paragraph from the Ruby README (the loop is where the agent
  actually does work).
- **New Files** table: `boukensha/agent.py`. **Updated Files** table:
  `boukensha/errors.py` (`LoopError`, unused — noted), `boukensha/client.py`
  (`tools` passthrough), `boukensha/prompt_builder.py` (`tools` passthrough
  + `parse_response`), all five `backends/*.py` (`tools` override +
  `parse_response` + `_assistant_message`/`_assistant_parts`),
  `boukensha/tasks/base.py` (`max_iterations`/`max_output_tokens`) —
  written from the Python port's own perspective, not copied from Ruby's
  table (which lists `backends/base.py`, `tasks/base.py`, `tasks/player.py`
  as "New Files," but those were already introduced in earlier Python
  steps).
- How It Works diagram (send → `stop_reason == "tool_use"`? → dispatch →
  inject results → loop, or return final text).
- `boukensha.Agent` method table (`run()`).
- **Every Backend Speaks the Same Normalized Shape** section — the
  `{stop_reason, content}` shape, the `parse_response` delegation, the
  reverse `_assistant_message`/`_assistant_parts` conversion on replay, and
  the tool-call-ID-isn't-universal note, all carried from the Ruby README
  (wire-format content, not language-specific).
- Task Configuration section — YAML sample with `max_iterations`/
  `max_output_tokens` added, and the provider/backend/required-env-var
  table.
- **What the Loop Looks Like** — captured from an actual run of the ported
  example (see verification step), not copied from the Ruby README's
  sample (which itself looks illustrative/hand-written rather than a
  captured run, given the tidy `[iteration 1]`/`[iteration 2]` shape).
- **Considerations** — all four Ruby bullets carried forward (assistant
  message before tool result; multiple tool calls per turn; `MAX_ITERATIONS`
  as a trigger threshold, not a hard cap; the agent can't stop itself
  unilaterally), since all four describe behavior, not Ruby syntax.
- **Run Example** pointing at `./week1_baseline/bin/python/05_agent_loop`.

### Launcher (`bin/python/05_agent_loop`, new)

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
cd "$SCRIPT_DIR/../../python/05_agent_loop"
"$REPO_ROOT/.venv/bin/python" examples/example.py
```

Needs `chmod +x` after creation.

## Cleanup

Nothing to clean up — this is a fresh directory, no leftover `__pycache__`
from a prior stale copy. Standard `__pycache__` cleanup after the
verification run still applies (gitignored, but tidy).

## Configuration Schema

Adds two optional keys under `tasks.player` — both already handled by
`Base.max_iterations`/`max_output_tokens` with sane defaults if omitted:

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

1. **`LoopError` is dead code in the Ruby reference — port it as dead code,
   or drop it?** As detailed in Design Considerations, nothing in
   `agent.rb` raises it; the max-iteration path always resolves to a
   string via `wrap_up`. Recommendation: port it into `errors.py` anyway
   (faithful 1:1 with `errors.rb`, and cheap enough that carrying unused
   dead code is less surprising than a Python `errors.py` that mysteriously
   has one fewer class than Ruby's). Confirm before implementation in case
   you'd rather leave it out until something actually uses it.
2. **This step can make *multiple* real API calls per run, not just one.**
   `04` made exactly one call. `05`'s loop makes one call per iteration
   until `stop_reason: "end_turn"` (or the 25-iteration ceiling triggers a
   wind-down call). The example's prompt ("read the README and summarize
   the framework") will plausibly take 2-3 round-trips (list/read the file,
   then a final summary) at real, if trivial, Haiku-tier cost. Flagging
   again since this compounds the same real-cost consideration from `04`'s
   Open Questions.
3. **Verification will actually execute `read_file`/`list_directory`
   against this repo's real filesystem.** Unlike `04`'s tools (which the
   model saw schemas for but never actually got to run, since there was no
   loop), `05`'s agent will really call `Registry.dispatch`, which really
   reads `05_agent_loop/README.md` and lists `05_agent_loop/`'s contents,
   and feeds genuine file contents back to the model. This is expected and
   is the whole point of the step, not a side effect to guard against — just
   confirming there's no reason to sandbox or mock it for this tutorial
   codebase.
