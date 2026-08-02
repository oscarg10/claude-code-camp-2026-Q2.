# Python Port Plan — 04 · The API Client

## Goal

Port `week1_baseline/ruby/04_api_client` to Python, replacing the contents
of `week1_baseline/python/04_api_client`. This step adds `Boukensha::Client`
— a stdlib-only HTTP client that takes the payload `PromptBuilder` already
assembles, POSTs it to whichever backend URL is active, retries transient
failures and retryable status codes, and raises a new `ApiError` on
anything that isn't eventually a 2xx. It also adds the actual live-request
example: register two real tools (`read_file`, `list_directory`), send one
real user message, and print the raw JSON response BOUKENSHA gets back
from the model.

## Starting state (found during planning)

`week1_baseline/python/04_api_client/` currently exists but is an
**unmodified copy of the `03_prompt_builder` port** — same leftover
copy-paste pattern called out in both prior plans:

- `README.md` is titled "03 · The Prompt Builder (Python)".
- `examples/example.py` still registers `look`/`move`, seeds a fabricated
  user/assistant/tool_result conversation, and stops at printing
  `builder.to_api_payload()` — it never sends anything anywhere.
- There is no `boukensha/client.py`.
- `boukensha/errors.py` has `UnknownToolError` and `UnsupportedModelError`
  only — `ApiError` is missing.
- `boukensha/__init__.py` doesn't export `Client`.
- `prompts/system.md` still has `03`'s "You are a MUD player assistant..."
  text, not this step's updated CircleMUD-flavored prompt.
- `week1_baseline/bin/python/04_api_client` **does not exist yet** — no
  launcher for this step at all (same situation `03` was in before this
  session, and the same situation `bin/ruby/04_api_client` was in until it
  was fixed earlier this session).

Everything else in `boukensha/` (`tool.py`, `message.py`, `context.py`,
`registry.py`, `prompt_builder.py`, all five `backends/*.py`,
`tasks/player.py`) is already correct and carries forward unchanged —
confirmed by diffing every Ruby `lib/` file in `04_api_client` against
`03_prompt_builder`'s: only `errors.rb`, `config.rb`, `tasks/base.rb`,
`boukensha.rb`, and `prompts/system.md` changed, and `client.rb` is
entirely new. `backends/*.rb` are byte-identical to `03`.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/04_api_client/README.md` | Spec/behaviour doc — `Client` method table, task config sample, response-shape JSON, and Considerations are ported from here |
| `week1_baseline/ruby/04_api_client/lib/boukensha/client.rb` | `Boukensha::Client` — HTTP POST with retry-on-transient-error and retry-on-retryable-status-code, wrapped in `ApiError` on final failure |
| `week1_baseline/ruby/04_api_client/lib/boukensha/errors.rb` | Adds `ApiError` alongside `UnknownToolError` and `UnsupportedModelError` |
| `week1_baseline/ruby/04_api_client/lib/boukensha/config.rb` | `PROMPTS_DIR` changed to a **three**-`".."` path (`"../../../prompts"`) — see Design Considerations, this looks like a bug, not intentional |
| `week1_baseline/ruby/04_api_client/lib/boukensha/tasks/base.rb` | `fetch` gains a `return nil unless settings.is_a?(Hash)` guard; error messages fixed from `"settings.yml"` to `"settings.yaml"` |
| `week1_baseline/ruby/04_api_client/lib/boukensha.rb` | Top-level require — now also requires `client`; individual backend requires no longer need a separate `backends/base` line (each backend file requires it directly) |
| `week1_baseline/ruby/04_api_client/prompts/system.md` | New default system prompt: CircleMUD-flavored, replacing `03`'s generic MUD-assistant text |
| `week1_baseline/ruby/04_api_client/examples/example.rb` | Runnable smoke-test — registers `read_file`/`list_directory` (real file-I/O tools, not scripted responses), seeds a single real user message, builds a backend from `settings.yaml`, and makes one live `Client#call`. Port line-for-line. |
| `week1_baseline/ruby/04_api_client/lib/boukensha/tool.rb`, `message.rb`, `context.rb`, `registry.rb`, `prompt_builder.rb`, `tasks/player.rb`, `backends/*.rb` | Unchanged from `03_prompt_builder` (diffed — identical) |
| `week1_baseline/ruby/04_api_client/Gemfile` / `Gemfile.lock` | Still just `dotenv` — no new dependency for `Client` (see "No Dependencies" in Ruby README) |

Also reference the already-completed `03_prompt_builder` port
(`week1_baseline/python/03_prompt_builder/`) for established Python
conventions this step continues: `is_prompt_override` naming, `#<...>`-style
`__str__` for parity, `_configure_model`/leading-underscore private helpers,
single `example.py`, shared root `.venv`.

## Design Considerations

- **`Client` is a new module, stdlib-only — `urllib.request`, not
  `requests`.** The Ruby README is explicit about this being intentional:
  *"To keep things explainable and simple we are using net/http... HTTPParty
  can solve this but we are trying to avoid any libraries."* Python's
  `urllib.request`/`urllib.error` are standard library, same as Ruby's
  `net/http` — no new line in `requirements.txt`, matching the Ruby step's
  "no gems, no bundle install."
- **Ruby's `Net::HTTP` always returns a response object; Python's
  `urlopen` raises on non-2xx.** This is a real control-flow divergence,
  not just syntax. Ruby's `call` checks
  `response.is_a?(Net::HTTPSuccess)` *after* the retry loop, uniformly for
  every status code. Python's `urllib.request.urlopen` raises
  `urllib.error.HTTPError` for any non-2xx response — so the Python port
  needs a `try/except urllib.error.HTTPError` *inside* the retry loop to
  capture `.code`/`.read()` off the exception before deciding whether to
  retry or fall through to raising `ApiError`. The retry decision logic and
  final error message are kept identical to Ruby's; only where the
  status/body get read from differs (response object vs. exception object).
- **`TRANSIENT_ERRORS` — one Python equivalent per Ruby class**, kept as an
  explicit tuple rather than collapsed into a single catch-all, to preserve
  the same "here are the specific things that can go wrong at the network
  layer" teaching value as Ruby's array:

  | Ruby | Python |
  |---|---|
  | `EOFError` | `EOFError` |
  | `Errno::ECONNRESET` | `ConnectionResetError` |
  | `Errno::ECONNREFUSED` | `ConnectionRefusedError` |
  | `Net::OpenTimeout` / `Net::ReadTimeout` | `TimeoutError` |
  | `OpenSSL::SSL::SSLError` | `ssl.SSLError` |
  | `SocketError` | `socket.gaierror` |
  | *(no single Ruby equivalent)* | `urllib.error.URLError` — added as a catch-all, since `urlopen` wraps most of the above into a `URLError` rather than letting them propagate raw; must be listed in a *separate, later* `except` clause than `HTTPError` since `HTTPError` is itself a `URLError` subclass and Python matches the first applicable clause |
- **SSL/cert handling needs zero extra code in Python — this directly
  resolves the exact problem `client.rb`'s own comments are wrestling
  with.** The Ruby file's comments (lines 30-33, discussed earlier this
  session) document a real rough edge: `OpenSSL::X509::DEFAULT_CERT_FILE`
  pointed at a macOS-only path that doesn't exist on Linux/WSL2, so it got
  commented out in favor of implicit system-cert discovery via
  `verify_mode = OpenSSL::SSL::VERIFY_PEER` alone. Python's
  `urllib.request.urlopen` on an `https://` URL already builds its SSL
  context via `ssl.create_default_context()`, which discovers system CA
  certs correctly on macOS, Linux, and Windows out of the box — there's no
  `ca_file` to set, comment out, or explain per-platform. Worth calling out
  in the Python README as the answer to the Ruby README's own "you will
  need to update the code based on your machine's requirements" caveat.
- **`Config.PROMPTS_DIR`'s Ruby `"../../../prompts"` looks like a
  directory-depth bug — don't port it.** Ruby 03 used
  `File.expand_path("../../prompts", __dir__)` (two `".."`, correctly
  landing at `<step>/prompts`). Ruby 04 changed this to
  `File.expand_path("../../../prompts", __dir__)` — a **third** `".."`,
  which from `lib/boukensha/config.rb`'s `__dir__` climbs past the step
  root entirely and lands at `week1_baseline/ruby/prompts` (one level
  above `04_api_client/`), a directory that doesn't exist. In practice this
  is currently masked because `.boukensha/settings.yaml` has
  `prompt_override.system: true` and a real user override file exists (as
  seen when we ran `03`'s port), so the broken default path is never
  actually read — `read_default_prompt` just returns `nil` silently rather
  than raising (guarded by `File.exist?`). But the Ruby README explicitly
  promises *"Otherwise it falls back to this step's shipped
  `prompts/system.md`"* — a promise the current Ruby code can't keep
  without a working default path. The Python port's `Config.PROMPTS_DIR`
  is **already correct** (two `.parent` calls, carried over unmodified from
  `03`, landing at `<step>/prompts` exactly as intended) — the
  recommendation is to leave it alone rather than "faithfully" reproduce a
  path that would break the step's own documented fallback behavior. See
  Open Questions.
- **`tasks/base.py._fetch` needs the new `isinstance` guard, and the error
  message typo fix.** Ruby's `fetch` now short-circuits to `nil` when
  `settings` isn't a `Hash` (defends against a task whose settings resolved
  to `nil`, e.g. a task name missing from `settings.yaml` entirely) —
  Python's `_fetch` gets the matching `isinstance(settings, dict)` guard.
  Separately, Ruby fixed `"settings.yml"` → `"settings.yaml"` in both the
  `provider` and `model` `ArgumentError` messages (the settings file has
  always been `.yaml`, this was just a stale string) — ported as a
  straightforward message-text fix, not a behavior change.
- **No fabricated conversation this time — one real user message.** Every
  prior step's example pre-seeded `ctx` with scripted user/assistant/
  tool_result turns to *demonstrate* payload shape without calling
  anything. `04`'s example seeds exactly one real `user` message
  (`"What files are in the current directory?"`) because the point of this
  step is an actual round trip — the model's real response is what
  demonstrates the payload shape now, not a hand-written fixture.
- **Provider dispatch order changed from `03`'s** (`anthropic` / `ollama` /
  `ollama_cloud` / `openai` / `gemini`) **to `04`'s**
  (`anthropic` / `openai` / `gemini` / `ollama` / `ollama_cloud`) — cosmetic
  reordering in the Ruby source's `case`/`when`, ported for fidelity even
  though it has no behavioral effect.
- **`read_file`/`list_directory` are real file-I/O blocks, not string
  templates.** Both stay as single-expression `lambda`s (matching the
  established convention from `"shout"` in `02` and `"move"` in `03`):
  `lambda path: Path(path).read_text()` and a `lambda path: "\n".join(...)`
  filtering out dotfiles. Ruby's `Dir.entries` has no guaranteed sort
  order and the Ruby block doesn't sort either — Python's `os.listdir`
  is ported the same way (unsorted), rather than "improving" it with a
  `sorted()` call that Ruby's own code doesn't have.
- **The Ruby README's "Output eaxmple" section is a stale personal
  transcript, not this step's actual output — don't copy it verbatim.**
  It shows a prompt (`andrew ~/Sites/Claude-Code-Camp/iterations $ ruby
  03_api_client/examples/step3.rb`) referencing a different path, a
  different step number, and a different (`claude-opus-4-5-20251101`)
  model than what `settings.yaml` in this repo actually configures, plus a
  typo in the section heading itself (*"eaxmple"*). Same situation as `02`'s
  README sample-output mismatch: rather than fabricate a matching transcript
  or copy one that's provably from a different run, the Python README's
  expected-output section is written from what the ported code actually
  prints, captured by running it (real API key already present in
  `.boukensha/.env`, confirmed working in this session's `03` port).

## Target file layout

```
week1_baseline/python/04_api_client/
  requirements.txt                 # unchanged: PyYAML, python-dotenv
  README.md                        # rewritten for this step (currently copy of 03's)
  prompts/
    system.md                      # updated: CircleMUD-flavored default prompt
  boukensha/
    __init__.py                    # adds Client
    config.py                      # unchanged from 03_prompt_builder (see PROMPTS_DIR note above)
    tool.py                        # unchanged from 03_prompt_builder
    message.py                     # unchanged from 03_prompt_builder
    context.py                     # unchanged from 03_prompt_builder
    errors.py                      # adds ApiError
    registry.py                    # unchanged from 03_prompt_builder
    prompt_builder.py              # unchanged from 03_prompt_builder
    client.py                      # new: Client
    backends/
      __init__.py                  # unchanged
      base.py                      # unchanged from 03_prompt_builder
      anthropic.py                 # unchanged from 03_prompt_builder
      ollama.py                    # unchanged from 03_prompt_builder
      ollama_cloud.py              # unchanged from 03_prompt_builder
      openai.py                    # unchanged from 03_prompt_builder
      gemini.py                    # unchanged from 03_prompt_builder
    tasks/
      __init__.py                  # unchanged
      base.py                      # updated: settings.is_a?(Hash) guard, "settings.yaml" message fix
      player.py                    # unchanged from 03_prompt_builder
  examples/
    example.py                     # rewritten for this step (currently copy of 03's)
week1_baseline/bin/python/04_api_client   # new launcher (doesn't exist yet)
```

## Porting notes (Ruby → Python mapping)

### `errors.py` — add `ApiError`

```python
class UnknownToolError(Exception):
    pass


class ApiError(Exception):
    pass


class UnsupportedModelError(Exception):
    pass
```

### `tasks/base.py` — `_fetch` guard + message fix

```python
@classmethod
def provider(cls, settings):
    value = cls._fetch(settings, "provider")
    if value is None:
        raise ValueError(f"tasks.{cls.task_name()}.provider is required in settings.yaml")
    return value

@classmethod
def model(cls, settings):
    value = cls._fetch(settings, "model")
    if value is None:
        raise ValueError(f"tasks.{cls.task_name()}.model is required in settings.yaml")
    return value

...

@classmethod
def _fetch(cls, settings, key):
    if not isinstance(settings, dict):
        return None
    return settings.get(key)
```

(Only the two error-message strings and `_fetch`'s new guard change;
`is_prompt_override`, `prompt`, `system_prompt`, `_read_user_prompt`,
`_read_default_prompt`, `_read_file` are untouched.)

### `prompts/system.md` — updated default prompt

```
You are Boukensha, an autonomous player exploring a CircleMUD world.

Use available tools to observe the world, act deliberately, and explain only what matters for the current turn.
```

### `client.py` (`client.rb` → `client.py`)

```ruby
require "net/http"
require "json"
require "openssl"

module Boukensha
  class Client
    RETRYABLE_STATUS_CODES = [408, 409, 429, 500, 502, 503, 504].freeze
    TRANSIENT_ERRORS = [
      EOFError, Errno::ECONNRESET, Errno::ECONNREFUSED,
      Net::OpenTimeout, Net::ReadTimeout, OpenSSL::SSL::SSLError,
      SocketError, Timeout::Error
    ].freeze
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def initialize(builder)
      @builder = builder
    end

    def call(max_output_tokens: 1024)
      uri          = URI(@builder.url)
      http         = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.verify_mode = OpenSSL::SSL::VERIFY_PEER

      request      = Net::HTTP::Post.new(uri, @builder.headers)
      request.body = @builder.to_api_payload(max_output_tokens: max_output_tokens).to_json

      attempts = 0
      response = nil

      loop do
        attempts += 1

        begin
          response = http.request(request)
        rescue *TRANSIENT_ERRORS => e
          raise ApiError, "API request failed after #{attempts} attempts: #{e.class}: #{e.message}" if attempts > MAX_RETRIES

          sleep retry_delay(attempts)
          next
        end

        if retryable_response?(response) && attempts <= MAX_RETRIES
          sleep retry_delay(attempts)
          next
        end

        break
      end

      unless response.is_a?(Net::HTTPSuccess)
        raise ApiError, "API request failed after #{attempts} attempt#{'s' unless attempts == 1} (#{response.code}): #{response.body}"
      end

      JSON.parse(response.body)
    end

    private

    def retryable_response?(response)
      RETRYABLE_STATUS_CODES.include?(response.code.to_i)
    end

    def retry_delay(attempt)
      BASE_RETRY_DELAY * (2**(attempt - 1))
    end
  end
end
```

```python
import json
import socket
import ssl
import time
import urllib.error
import urllib.request

from .errors import ApiError


class Client:
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    TRANSIENT_ERRORS = (
        EOFError,
        ConnectionResetError,
        ConnectionRefusedError,
        TimeoutError,
        ssl.SSLError,
        socket.gaierror,
        urllib.error.URLError,
    )
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder):
        self.builder = builder

    def call(self, max_output_tokens=1024):
        payload = json.dumps(
            self.builder.to_api_payload(max_output_tokens=max_output_tokens)
        ).encode("utf-8")
        request = urllib.request.Request(
            self.builder.url(),
            data=payload,
            headers=self.builder.headers(),
            method="POST",
        )

        attempts = 0
        response_code = None
        response_body = None

        while True:
            attempts += 1

            try:
                with urllib.request.urlopen(request) as response:
                    response_code = response.status
                    response_body = response.read()
            except urllib.error.HTTPError as e:
                response_code = e.code
                response_body = e.read()
            except self.TRANSIENT_ERRORS as e:
                if attempts > self.MAX_RETRIES:
                    raise ApiError(
                        f"API request failed after {attempts} attempts: {type(e).__name__}: {e}"
                    ) from e

                time.sleep(self._retry_delay(attempts))
                continue

            if self._retryable_response(response_code) and attempts <= self.MAX_RETRIES:
                time.sleep(self._retry_delay(attempts))
                continue

            break

        if not (200 <= response_code < 300):
            suffix = "" if attempts == 1 else "s"
            raise ApiError(
                f"API request failed after {attempts} attempt{suffix} "
                f"({response_code}): {response_body.decode('utf-8', errors='replace')}"
            )

        return json.loads(response_body)

    def _retryable_response(self, code):
        return code in self.RETRYABLE_STATUS_CODES

    def _retry_delay(self, attempt):
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
```

Notes on the non-mechanical lines:

- `urllib.request.urlopen` raises `HTTPError` for any non-2xx response
  instead of returning it — the Python `try/except` structure inside the
  loop replaces Ruby's post-loop `unless response.is_a?(Net::HTTPSuccess)`
  check with an equivalent `if not (200 <= response_code < 300)` after the
  loop, fed by whichever branch (success or `HTTPError`) set
  `response_code`/`response_body`.
- No `http.use_ssl` / `verify_mode` lines needed — `urlopen` picks HTTPS
  automatically from the URL scheme and verifies certs by default (see
  Design Considerations).
- `Net::HTTP::Post.new(uri, @builder.headers)` → `urllib.request.Request(...,
  headers=self.builder.headers(), method="POST")` — headers dict passed
  straight through; `Content-Type` is already part of each backend's
  `headers()` dict, same as in Ruby.

### `boukensha/__init__.py` — add `Client`

```python
from .backends.anthropic import Anthropic
from .backends.gemini import Gemini
from .backends.ollama import Ollama
from .backends.ollama_cloud import OllamaCloud
from .backends.openai import OpenAI
from .client import Client
from .config import Config
from .context import Context
from .errors import ApiError, UnknownToolError, UnsupportedModelError
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

__all__ = [
    "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "UnknownToolError", "UnsupportedModelError",
    "Message", "PromptBuilder", "Registry", "Player", "Tool",
]
```

### Example (`example.rb` → `examples/example.py`)

```python
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boukensha import (
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

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

registry.tool(
    "read_file",
    description="Read the contents of a file from disk",
    parameters={"path": {"type": "string", "description": "The file path to read"}},
    block=lambda path: Path(path).read_text(),
)

registry.tool(
    "list_directory",
    description="List files in a directory",
    parameters={"path": {"type": "string", "description": "The directory path to list"}},
    block=lambda path: "\n".join(entry for entry in os.listdir(path) if not entry.startswith(".")),
)

ctx.add_message("user", "What files are in the current directory?")

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

print("=== BOUKENSHA Step 4: API Client ===")
print()
print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print(f"Sending request to {builder.url()}...")
print()

response = client.call()
print("Raw response:")
print(json.dumps(response, indent=2))
```

### `README.md`

Rewritten for this step, following the Python README structure established
in `01`-`03`, replacing the Prompt-Builder-focused body with:

- Overview paragraph from the Ruby README (one HTTP POST, one response, no
  tool loop yet).
- A **New Files / Updated Files** table written from the Python port's own
  perspective (not copied verbatim from Ruby's, since `backends/base.py`,
  `tasks/base.py`, and `tasks/player.py` were already introduced in earlier
  Python steps): New — `boukensha/client.py`. Updated —
  `boukensha/errors.py` (adds `ApiError`), `boukensha/tasks/base.py`
  (`Hash`/`dict` guard + message fix), `prompts/system.md` (new default
  prompt), `examples/example.py`, `README.md`.
- `boukensha.Client` method table (`call(max_output_tokens=1024)`).
- Task Configuration section — same YAML sample.
- **No Dependencies** section, adapted: `Client` uses Python's standard
  `urllib.request` — no third-party HTTP library, no new
  `requirements.txt` entry.
- **What the Response Looks Like** — the Anthropic/Ollama JSON samples
  carry over unchanged (wire format, not language-specific), plus the note
  about `stop_reason: "tool_use"` / `tool_calls` being step 5's concern.
- **Considerations** — the two behavior bullets carried forward
  (`ApiError` on failure; SSL handled automatically for `https`), plus a
  replacement for the Ruby "OpenSSL Certificate" bullet: instead of "you
  will need to update the code based on your machine's requirements,"
  explain that `urllib`'s default HTTPS context already resolves system
  certs on every platform, so there's nothing to configure — directly
  answering the rough edge the Ruby version warns about.
- **Run Example** output captured from actually running the ported code
  (real `ANTHROPIC_API_KEY` already present in `.boukensha/.env`), rather
  than the Ruby README's stale personal-terminal transcript — see Design
  Considerations.
- Updated **Run Example** command pointing at
  `./week1_baseline/bin/python/04_api_client`.

### Launcher (`bin/python/04_api_client`, new)

Doesn't exist yet. Create following the established fixed pattern:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../../.."
cd "$SCRIPT_DIR/../../python/04_api_client"
"$REPO_ROOT/.venv/bin/python" examples/example.py
```

Needs `chmod +x` after creation, matching the other launchers.

## Cleanup

- Delete any stray `__pycache__/` directories currently sitting in
  `python/04_api_client/` (leftover from running the stale `03`-copy) —
  confirmed present under `boukensha/__pycache__/`,
  `boukensha/tasks/__pycache__/`, and `boukensha/backends/__pycache__/`.

## Configuration Schema

Unchanged in shape from `03` — still `tasks.player.provider` /
`tasks.player.model` / `tasks.player.prompt_override.system`. No new keys.
This step will make a **real, billed** API call when run (unlike `01`-`03`,
which only built payloads locally) — worth a one-line heads-up in the
README's Run Example section, not a schema change.

## Open Questions

1. **Confirmed carried over from `03`: port `PromptBuilder`'s one-arg
   `to_messages`/`to_tools` arity mismatch faithfully.** Unchanged this
   step — `prompt_builder.rb`/`.py` aren't touched by `04` at all, and the
   example still only calls `to_api_payload`, so this remains dormant.
   No new decision needed here, just confirming it doesn't resurface.
2. **`Config.PROMPTS_DIR`'s extra `".."` in Ruby 04 — treat as a bug, not
   a step-specific redesign?** As detailed in Design Considerations, the
   literal Ruby path change breaks the step's own documented default-prompt
   fallback (currently masked by the user's `prompt_override` being
   active). Recommendation: leave the Python `PROMPTS_DIR` alone (it
   already does the right thing, inherited correctly from `03`) rather
   than reproducing the extra `".."`. Confirm before implementation, since
   this is a case where "faithful port" and "working code" diverge and the
   Ruby reference itself looks unintentionally broken rather than
   deliberately teaching something.
3. **This step makes a real API call — confirm you want it to run for
   real during verification.** Given `ANTHROPIC_API_KEY` is now set and
   `03`'s port already proved the Anthropic backend/payload path works,
   running `04`'s ported example will send one small live request to
   `https://api.anthropic.com/v1/messages` (a `read_file`/`list_directory`
   tool-enabled prompt, `max_output_tokens` defaulting to 1024) and consume
   a trivial amount of real Haiku-tier usage. Flagging this explicitly
   before implementation since — unlike every step so far — this one isn't
   free to verify.
