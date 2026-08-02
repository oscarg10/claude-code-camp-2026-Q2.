# 04 · The API Client (Python)

## Setup

This step (and every later Python step) shares a single virtualenv at the
**repo root**, so it only needs to be created once:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r week1_baseline/python/04_api_client/requirements.txt
```

The launcher at `week1_baseline/bin/python/04_api_client` assumes `.venv`
already exists at the repo root and has these dependencies installed.

---

The API Client takes the payload assembled by `PromptBuilder` and sends it
to the API. One HTTP POST, one response. No tool loop yet — just proving
the round trip works.

## New Files

| File | Description |
|---|---|
| `boukensha/client.py` | Makes the HTTP request and parses the response |

## Updated Files

| File | Change |
|---|---|
| `boukensha/errors.py` | Added `ApiError` for failed HTTP requests |
| `boukensha/tasks/base.py` | `_fetch` now guards against a non-`dict` settings value; error messages fixed from `settings.yml` to `settings.yaml` |
| `prompts/system.md` | New default system prompt (CircleMUD-flavored) |

`boukensha/backends/base.py` and `boukensha/tasks/player.py` were already
introduced in earlier Python steps (`03_prompt_builder`), unlike the Ruby
tutorial's own step numbering — they carry forward unchanged here.

## How It Works

```
PromptBuilder
      ↓
Client
      ↓
POST to API endpoint
      ↓
Raw JSON response
```

## `boukensha.Client`

| Method | Description |
|---|---|
| `call(max_output_tokens=1024)` | POSTs the payload and returns the parsed JSON response |

## Task Configuration

This step uses the task-based configuration introduced in the earlier
baseline steps:

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
```

When `prompt_override.system` is true, Boukensha reads
`.boukensha/prompts/player/system.md`. Otherwise it falls back to this
step's shipped `prompts/system.md`.

Each backend validates the configured model at construction time.
Unsupported model names raise `UnsupportedModelError`, and supported models
expose backend-owned metadata such as `context_window`, `usage_unit`, and
token cost estimates for later logging steps.

## No Dependencies

`Client` uses Python's standard `urllib.request`/`urllib.error` modules. No
third-party packages, no new line in `requirements.txt`. This is
intentional — the HTTP call itself is trivial and should be visible, not
hidden behind a library.

## What the Response Looks Like

The raw response shape differs between backends. This is what you get back
from `client.call()` before any processing:

### Anthropic
```json
{
  "id": "msg_01XY",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Sure, let me read that file." }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 42, "output_tokens": 18 }
}
```

### Ollama
```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "Sure, let me read that file."
  },
  "done_reason": "stop",
  "done": true
}
```

When the model wants to call a tool the response looks different. Anthropic
uses `stop_reason: "tool_use"` and adds a `tool_use` block to `content`.
Ollama adds a `tool_calls` array to `message`. Handling those differences
is the job of step 5 — the Agent Loop.

## Considerations

**The client raises `ApiError` on failure.** A non-2xx response means
something went wrong — bad API key, malformed payload, server error.
BOUKENSHA surfaces this explicitly rather than returning a confusing `None`
or partial response.

**SSL is handled automatically — with no extra code needed.** Python's
`urllib.request` builds its HTTPS context via
`ssl.create_default_context()`, which discovers the system's CA
certificates correctly on macOS, Linux, and Windows without any explicit
`ca_file` path. Ollama running locally uses plain `http`, so no SSL is
involved there at all.

This is worth calling out because the Ruby version of this same file has
comments documenting the opposite experience: an explicit
`OpenSSL::X509::DEFAULT_CERT_FILE` path that worked on macOS but pointed at
a file (`/usr/lib/ssl/cert.pem`) that doesn't exist on Linux/WSL2, later
removed in favor of implicit system-cert discovery. Python's `urlopen`
never needed that workaround in the first place — there's no per-platform
cert path to configure.

## Run Example

```sh
./week1_baseline/bin/python/04_api_client
```

Example output (a live call — the exact response depends on the model and
what files are actually in your working directory):

```
=== BOUKENSHA Step 4: API Client ===

Config: #<Boukensha::Config dir=.../.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Sending request to https://api.anthropic.com/v1/messages...

Raw response:
{
  "model": "claude-haiku-4-5-20251001",
  "id": "msg_011Cde4zihki9HdsoQyHgxyG",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll list the files in the current directory for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_013A1EC59WPpAMgysAY27y2H",
      "name": "list_directory",
      "input": {
        "path": "."
      },
      "caller": {
        "type": "direct"
      }
    }
  ],
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "stop_details": null,
  "usage": {
    "input_tokens": 695,
    "output_tokens": 65,
    ...
  }
}
```

The model saw both `read_file` and `list_directory` tool schemas, correctly
picked `list_directory` for "what files are in the current directory?", and
stopped with `stop_reason: "tool_use"` — it never actually got to run the
tool, because there's no loop yet to execute it and send the result back.
That's step 5.
