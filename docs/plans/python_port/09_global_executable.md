# Python Port Plan — 09 · Global Executable

## Goal

Port `week1_baseline/ruby/09_global_executable` to Python, creating
`week1_baseline/python/09_global_executable`. This step is different in
kind from every step before it: `00`-`08` each added a capability to
`Boukensha` itself (config, registry, the agent loop, logging, the run
DSL, the REPL). `09` adds nothing to the library — it packages what
already exists so a command works from anywhere on the machine, without
`cd`-ing into a step folder and invoking a language runtime by hand.

The Ruby reference does this with a gem (`boukensha.gemspec`, `bin/boukensha`,
`gem build && gem install`). Python has no direct equivalent of a gem, so
this plan adapts the same three-piece shape — **loader** (resolves which
step's code to run), **bundled default** (a fallback copy baked in at
"build" time), **installable entry point** (what actually lands on `$PATH`)
— to Python's own packaging idioms (`pyproject.toml` + `pip install -e .`)
rather than force-fitting Ruby's gem mechanics.

**Command name: `boukensha-py`, not `boukensha`.** The Ruby gem's
`boukensha` command is already installed and in daily use (set up earlier
this session — `~/.boukensharc` points it at the live
`ruby/08_the_repl_loop`). The two languages can't share one command name,
so this port uses a distinct one throughout — including distinct env
var/rc-file names where a shared name would be ambiguous (see Design
Considerations).

## Starting state (found during planning)

`week1_baseline/python/09_global_executable/` doesn't exist yet.
`week1_baseline/bin/python/09_global_executable` and
`week1_baseline/bin/ruby/09_global_executable` don't exist either — and
that's correct, not a gap to fill. Every step `00`-`08` has a
`bin/<lang>/<step>` launcher because those steps are meant to be run
in-place inside the repo. `09` is meant to be *installed*; there's nothing
for a repo-relative launcher script to do here, matching how the Ruby side
also has no `bin/ruby/09_global_executable`.

## Reference files (source of truth — read these before porting)

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/09_global_executable/README.md` | Spec/behaviour doc — **contains stale directory names and a stale gem filename**, see Design Considerations |
| `week1_baseline/ruby/09_global_executable/boukensha.gemspec` | Declares the gem: name, version (from `VERSION`), which files ship, the `bin/boukensha` executable |
| `week1_baseline/ruby/09_global_executable/bin/boukensha` | Three-line shebang script: unshift `lib/` onto `$LOAD_PATH`, `require "boukensha_loader"`, call `BoukenshaLoader.load_and_start_repl` |
| `week1_baseline/ruby/09_global_executable/lib/boukensha_loader.rb` | The actual logic: 3-tier resolution (`BOUKENSHA_PATH` → `~/.boukensharc` → bundled default), debug logging, REPL-support check, starts `Boukensha.repl` |
| `week1_baseline/ruby/09_global_executable/lib/boukensha.rb` + `lib/boukensha/*.rb` | The bundled default — a **snapshot copy** of `08_the_repl_loop`'s lib, frozen at gem-build time. **Not identical to `08`'s current code** — see Design Considerations, this is the crux of the step |
| `week1_baseline/ruby/09_global_executable/Gemfile` / `Gemfile.lock` | `gemspec` + `dotenv` — the gem depends on itself via the local `PATH` source, matching how a Python editable install works |

Also reference the already-completed `08_the_repl_loop` port
(`week1_baseline/python/08_the_repl_loop/`) — the bundled default's
`boukensha/` package is built starting from a copy of that step's
`boukensha/`, `prompts/`, and `requirements.txt`.

## Design Considerations

- **The Ruby README has two stale-doc issues worth knowing about, not
  porting.** `## Install` says `cd 08_global_executable` — the real
  directory is `09_global_executable`. It also says
  `gem install boukensha-0.1.0.gem` — the actually-built gem in this repo
  is `boukensha-0.9.0.gem` (confirmed against `lib/boukensha/version.rb`
  and the `.gem` file already sitting in that folder). The `BOUKENSHA_PATH`
  examples reference `07_the_repl_loop` and `06_the_run_dsl`, which don't
  exist in this repo — the real ones are one number higher
  (`08_the_repl_loop`, `07_the_run_dsl`). Same stale-documentation pattern
  this whole series keeps finding; the Python README uses this repo's
  actual paths throughout.
- **The bundled-default lib inside `09_global_executable` is not a clean
  copy of `08`'s code — it's a snapshot with three real regressions,
  confirmed by diffing them directly:**
  1. `client.rb` — the 401-specific `"authentication failed... check your
     API key"` message (added in `08`) is **gone**; a 401 gets the
     generic failure message again.
  2. `config.rb` — `resolve_dir`'s CWD-`.boukensha` tier (added in `08`)
     is **gone**; back to a plain 2-tier `BOUKENSHA_DIR` → `~/.boukensha`.
  3. `repl.rb`'s `banner` — the richer `key_status`/`config_exists`
     computation (API-key-set checkmark, "directory not found" warning) is
     **gone**, replaced with a plainer three-line `config:`/`provider:`/
     `model:` block that doesn't surface either signal.
  This reads exactly like `06`/`07`'s `mud_*`/`LoopError` back-and-forth —
  the bundled snapshot was taken from an earlier point than `08`'s final
  state. Following this whole series' established stance (port the
  reference's actual state, note the regression, don't silently "fix" it),
  the Python bundled default mirrors these same three regressions relative
  to `08_the_repl_loop` — not `08`'s more advanced behavior. This matters
  less here than it did for `00`-`08`, though: the bundled default is a
  *fallback*, and this plan's own recommended setup (below) points
  `boukensha-py` at the live `08` folder instead, same as was just done for
  the Ruby `boukensha` command — so in practice the regressions don't
  affect daily use, only what you get if you run `boukensha-py` with no
  override configured at all.
- **No gem equivalent — Python packaging uses `pyproject.toml` +
  `pip install -e .`, and that's a genuine improvement on one front.**
  `gem build && gem install` copies files into a versioned gem archive —
  a real, frozen snapshot, disconnected from the source tree; picking up
  a code change means rebuilding and reinstalling. `pip install -e .`
  (editable install) instead adds the source directory itself to the
  Python path — so even the *bundled default* stays live: editing
  `python/09_global_executable/boukensha/*.py` directly takes effect on
  the next `boukensha-py` invocation, no reinstall needed. Worth noting as
  a real behavioral difference from Ruby's gem, not just a mechanical
  translation.
- **Distinct env var and rc-file names for the Python track — not a
  reuse of Ruby's `BOUKENSHA_PATH` / `~/.boukensharc`.** `BOUKENSHA_PATH`
  and `~/.boukensharc` are already in active use, pointing the Ruby
  `boukensha` command at a folder containing `lib/boukensha.rb`. If
  `boukensha-py`'s loader also read `BOUKENSHA_PATH`/`~/.boukensharc`, two
  ambiguous failure modes follow: whichever tool runs second sees a path
  meant for the other language and fails confusingly (a Ruby step folder
  has no `boukensha/__init__.py`; a Python one has no `lib/boukensha.rb`),
  and there's no way to configure both tools to point at *different* step
  numbers simultaneously (e.g. Ruby pinned to `08`, Python still being
  worked on at an earlier step) without one clobbering the other. This
  plan uses `BOUKENSHA_PY_PATH` and `~/.boukensharc-py` — distinct names,
  same resolution order and semantics. `BOUKENSHA_DIR` (the *config*
  directory — `settings.yaml`, `.env`, prompt overrides) stays **shared**
  between both tools on purpose: the config format is language-agnostic,
  and pointing both at the same `.boukensha/` avoids duplicating API keys
  and settings. `BOUKENSHA_DEBUG` also stays shared (same purpose, same
  trigger, only the printed prefix differs: `[boukensha-py]` vs
  `[boukensha]`).
- **The loader uses `importlib.util.spec_from_file_location`, not a bare
  `sys.path.insert` + `import boukensha`.** A naive line-for-line port of
  Ruby's `$LOAD_PATH.unshift` + `require` would insert the resolved step
  directory at the front of `sys.path` and then `import boukensha`. That
  works most of the time, but it's fragile in a way Ruby's version isn't:
  the loader's *own* bundled `boukensha/` package sits right next to
  `boukensha_loader.py` on disk, and depending on install/invocation
  details, relying on `sys.path` ordering to pick the *right* one of
  potentially several same-named `boukensha` packages is exactly the kind
  of ambient, order-dependent behavior Python's import system is prone to
  getting wrong silently. The loader instead resolves the target step's
  `boukensha/__init__.py` to an absolute path and loads it explicitly via
  `importlib.util.spec_from_file_location` / `module_from_spec` /
  `exec_module`, registering the result in `sys.modules["boukensha"]` —
  deterministic regardless of what else happens to be importable, and the
  more idiomatic Python mechanism for "load this specific package from
  this specific path" (a real 08-generation loader running against, say, a
  `BOUKENSHA_PY_PATH` pointed at a future `10_...` step doesn't risk
  accidentally picking up `09`'s own bundled copy instead).
- **`pyproject.toml` uses plain `setuptools` as the build backend, not
  `hatchling` or `uv`.** `circlemud-world-parser` (this repo's only other
  Python project) uses `hatchling` + `uv`-style dependency groups, but
  `00_config`'s plan already made an explicit, deliberate call for this
  whole port series: pip + `requirements.txt`, no `uv`/`poetry` lockfile
  tooling. `09` is the first step that genuinely needs *some* packaging
  metadata (a console-script entry point isn't expressible via
  `requirements.txt` alone), but it stays as minimal as possible —
  `setuptools` is stdlib-adjacent and needs no new project-wide tooling
  decision, consistent with the "pip first" stance already on record.
- **`py-modules = ["boukensha_loader"]`, not `packages = find:`.**
  Setuptools' automatic package discovery would happily also install the
  bundled `boukensha/` directory as a real top-level `boukensha` package
  into the venv's `site-packages` — which is exactly the ambiguity the
  `importlib`-based loader (above) is designed to avoid. The
  `pyproject.toml` explicitly lists only `boukensha_loader` as an
  installable module; `boukensha/` stays a plain sibling directory on disk
  that the loader locates relative to its own `__file__` (the direct
  Python analogue of Ruby's
  `BUNDLED_LIB = File.expand_path("../boukensha.rb", __FILE__)`), never a
  separately-importable package in its own right.
- **`requirements.txt` is kept for documentation/consistency, even though
  it's not load-bearing for this step.** Every other step's README says
  "`pip install -r requirements.txt`"; `09`'s actual install step is
  `pip install -e .`, and `pyproject.toml`'s own `dependencies` list
  already covers `PyYAML`/`python-dotenv` for that path. `requirements.txt`
  is included anyway, matching every prior step's file layout, but the
  README is explicit that `pip install -e .` is the real install command
  for this step specifically.

## Target file layout

```
week1_baseline/python/09_global_executable/
  pyproject.toml                   # new — console-script entry point, minimal setuptools backend
  requirements.txt                 # unchanged: PyYAML, python-dotenv (documentation-only here, see above)
  README.md                        # new
  boukensha_loader.py              # new — the loader (bundled-default resolution, debug logging, REPL-support check)
  prompts/
    system.md                      # unchanged from 08_the_repl_loop
  boukensha/                       # the bundled default — snapshot of 08_the_repl_loop, with the same 3 regressions Ruby's snapshot has
    __init__.py                    # unchanged from 08_the_repl_loop
    version.py                     # updated: VERSION = "0.9.0"
    config.py                      # updated: _resolve_dir reverts to the 2-tier form (matches Ruby's regression)
    client.py                      # updated: 401-specific message removed (matches Ruby's regression)
    repl.py                        # updated: banner reverts to the plainer 3-line form (matches Ruby's regression)
    context.py                     # unchanged from 08_the_repl_loop
    errors.py                      # unchanged from 08_the_repl_loop
    registry.py                    # unchanged from 08_the_repl_loop
    prompt_builder.py              # unchanged from 08_the_repl_loop
    logger.py                      # unchanged from 08_the_repl_loop
    agent.py                       # unchanged from 08_the_repl_loop
    run_dsl.py                     # unchanged from 08_the_repl_loop
    tool.py                        # unchanged from 08_the_repl_loop
    message.py                     # unchanged from 08_the_repl_loop
    backends/                      # unchanged from 08_the_repl_loop
    tasks/                         # unchanged from 08_the_repl_loop
```

No `week1_baseline/bin/python/09_global_executable` — see Starting state.

## Porting notes (Ruby → Python mapping)

### `boukensha_loader.py` (new) — the loader

```python
import importlib.util
import os
import sys
from pathlib import Path

# Absolute path to this file's own directory — the bundled default lives
# in a boukensha/ package right next to it, the direct analogue of Ruby's
# BUNDLED_LIB = File.expand_path("../boukensha.rb", __FILE__).
BUNDLED_DIR = Path(__file__).resolve().parent


def _has_package(step_dir):
    return (step_dir / "boukensha" / "__init__.py").exists()


def resolve():
    # 1. Env var wins.
    env_path = os.environ.get("BOUKENSHA_PY_PATH")
    if env_path:
        step_dir = Path(env_path).expanduser().resolve()
        if _has_package(step_dir):
            return step_dir
        sys.exit(
            f"boukensha-py: BOUKENSHA_PY_PATH is set but no boukensha/__init__.py found at:\n"
            f"       {step_dir}\n"
            f"       Make sure BOUKENSHA_PY_PATH points to a step folder, e.g.:\n"
            f"       BOUKENSHA_PY_PATH=~/Sites/boukensha/python/08_the_repl_loop boukensha-py"
        )

    # 2. ~/.boukensharc-py
    rc = Path("~/.boukensharc-py").expanduser()
    if rc.exists():
        raw = rc.read_text().strip()
        if raw:
            step_dir = Path(raw).expanduser().resolve()
            if _has_package(step_dir):
                return step_dir
            sys.exit(
                f"boukensha-py: ~/.boukensharc-py points to {raw}\n"
                f"       but no boukensha/__init__.py was found there.\n"
                f"       Update ~/.boukensharc-py or remove it to use the bundled default."
            )

    # 3. Bundled default.
    return BUNDLED_DIR


def _load_boukensha_package(step_dir):
    """Load step_dir/boukensha/__init__.py as the `boukensha` module,
    regardless of what else is importable — deterministic even if another
    boukensha/ package (e.g. this loader's own bundled copy) is nearby."""
    pkg_dir = step_dir / "boukensha"
    spec = importlib.util.spec_from_file_location(
        "boukensha", pkg_dir / "__init__.py", submodule_search_locations=[str(pkg_dir)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["boukensha"] = module
    spec.loader.exec_module(module)
    return module


def main():
    step_dir = resolve()

    if os.environ.get("BOUKENSHA_DEBUG"):
        print(f"[boukensha-py] loading from: {step_dir}")

    boukensha = _load_boukensha_package(step_dir)

    if not hasattr(boukensha, "repl"):
        sys.exit(
            f"boukensha-py: the step at {step_dir}\n"
            f"       does not support the interactive REPL (added in step 08).\n"
            f"       Run its examples directly, e.g.:\n"
            f"         python {step_dir}/examples/example.py\n"
            f"       Or point BOUKENSHA_PY_PATH at step 08 or later."
        )

    boukensha.repl()


if __name__ == "__main__":
    main()
```

Notes on the non-mechanical lines:

- Ruby's `abort <<~MSG ... MSG` (prints to stderr, exits nonzero) →
  `sys.exit(f"...")` — `sys.exit` with a string argument prints it to
  stderr and exits with status 1, the same shape.
- `Boukensha.respond_to?(:repl)` → `hasattr(boukensha, "repl")` — both ask
  "does the loaded module/object expose this callable," same purpose:
  detecting a pre-`08` step (no REPL support) and failing with a
  actionable message instead of an `AttributeError`.
- `File.dirname(File.dirname(main))` (Ruby derives the step directory from
  the resolved `lib/boukensha.rb` path) has no equivalent step here —
  `resolve()` already returns the step *directory* directly, not a path to
  a specific file inside it, since Python's target is a package directory
  (`boukensha/__init__.py`) rather than a single require-target file.

### `pyproject.toml` (new)

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "boukensha-py"
version = "0.9.0"
description = "BOUKENSHA — a tiny teaching framework for coding harnesses (Python port)"
requires-python = ">=3.10"
dependencies = [
    "PyYAML",
    "python-dotenv",
]

[project.scripts]
boukensha-py = "boukensha_loader:main"

[tool.setuptools]
py-modules = ["boukensha_loader"]
```

`version` is kept in sync with `boukensha/version.py`'s `VERSION` by hand
(Ruby's gemspec reads `Boukensha::VERSION` programmatically via
`require_relative "lib/boukensha/version"`; `pyproject.toml` is static
TOML with no code execution, so there's no direct equivalent — this is a
real, permanent divergence, not a temporary shortcut, and is called out in
the README so it doesn't silently drift).

### Bundled default `boukensha/` package — the three regressions

Starting from a copy of `08_the_repl_loop`'s `boukensha/`:

**`version.py`**
```python
VERSION = "0.9.0"
```

**`config.py`** — `_resolve_dir` reverts to 2-tier:
```python
def _resolve_dir(self):
    raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
    return str(Path(raw).expanduser().resolve())
```
(Drops the `Path.cwd() / ".boukensha"` tier `08` added — matches Ruby's
`09` snapshot exactly, including the docstring reverting to describe only
2 tiers.)

**`client.py`** — drop the 401-specific branch:
```python
if not (200 <= response_code < 300):
    suffix = "" if attempts == 1 else "s"
    raise ApiError(
        f"API request failed after {attempts} attempt{suffix} "
        f"({response_code}): {response_body.decode('utf-8', errors='replace')}"
    )
```

**`repl.py`** — `_banner` reverts to the plainer form:
```python
def _banner(self):
    ver = self.version or "?.?.?"
    padding = " " * (9 - len(ver))

    return (
        "\n"
        "╔══════════════════════════════════════╗\n"
        f"║  BOUKENSHA MUD Assistant (v{ver}){padding}║\n"
        "╚══════════════════════════════════════╝\n"
        f"  config:        {self.config_dir or '(default)'}\n"
        f"  provider:      {self.provider or '(default)'}\n"
        f"  model:         {self.model or '(default)'}\n"
        "\n"
        "  /quiet or /loud   toggle logging\n"
        "  /clear           reset conversation history\n"
        "  /exit or /quit    leave the REPL\n"
        "\n"
    )
```
(No more `key_status`/`config_exists`/`provider_line` — matches Ruby's
`09` snapshot losing the API-key-set indicator and the "directory not
found" warning.)

Everything else in the bundled `boukensha/` package —
`__init__.py`, `context.py`, `errors.py`, `registry.py`,
`prompt_builder.py`, `logger.py`, `agent.py`, `run_dsl.py`, `tool.py`,
`message.py`, `backends/*.py`, `tasks/*.py` — is a byte-for-byte copy of
`08_the_repl_loop`'s, unchanged.

### `README.md`

New file. Structure:

- What this step adds (loader, bundled default, entry point — framed as
  "packaging, not new capability," same framing as the Ruby README's own
  opening line).
- **Install** — the real commands, using this repo's actual paths:
  ```bash
  cd week1_baseline/python/09_global_executable
  pip install -e .
  ```
  (run inside the shared repo-root `.venv`, per every prior step's Setup
  convention) — explicitly *not* `pip install -r requirements.txt` for
  this step, with a one-line note on why.
- **Switching steps with `BOUKENSHA_PY_PATH`** — table mirroring the Ruby
  README's, with corrected paths and the Python-specific env
  var/rc-file names, plus the note that `BOUKENSHA_DIR` and
  `BOUKENSHA_DEBUG` are shared with the Ruby `boukensha` command on
  purpose.
- **Recommended setup for this repo** — concretely: point
  `~/.boukensharc-py` at `week1_baseline/python/08_the_repl_loop` (the
  live, editable folder — same reasoning already applied to the Ruby
  `boukensha` command's `~/.boukensharc`), not the bundled default, so
  `boukensha-py` reflects ongoing edits without a reinstall.
- **The bundled default's known regressions** — the three differences
  from live `08` listed in Design Considerations, so running
  `boukensha-py` with no override configured doesn't read as broken.
- **The key idea** section, adapted from the Ruby README's closing
  paragraph (the package is a wrapper and a default; it doesn't copy or
  symlink the numbered step folders, it just knows where to look —
  literally true for Python too, arguably more so given the editable
  install).

## Cleanup

Nothing to clean up — fresh directory. No `__pycache__` concerns beyond
the standard post-verification sweep.

## Configuration Schema

Unchanged — this step reads the same `tasks.player` shape as `08`, via
whichever `boukensha/` package ends up loaded. No new `settings.yaml` keys.

## Open Questions

1. **`BOUKENSHA_PY_PATH` / `~/.boukensharc-py` naming.** This plan commits
   to distinct names to avoid collision with the already-configured Ruby
   `boukensha` command (detailed in Design Considerations). Confirm before
   implementation in case a different naming scheme is preferred (e.g. a
   single shared `BOUKENSHA_PATH` where the loader disambiguates by
   checking for `lib/boukensha.rb` vs `boukensha/__init__.py` at the
   target — technically workable, but adds a silent-guessing failure mode
   this plan avoids by just using different names).
2. **Should the bundled default actually carry the three regressions, or
   should this port "fix" them since they only affect the low-stakes
   fallback path?** This plan follows the series' established
   don't-second-guess-the-reference stance and ports them faithfully,
   flagged clearly rather than silently diverging. Worth confirming since
   the stakes are genuinely lower here than in `00`-`08` (the fallback
   isn't what `README.md`'s own recommended setup tells you to rely on).
3. **`pyproject.toml`'s `version` field must be updated by hand
   alongside `boukensha/version.py`** — there's no automatic sync
   mechanism the way Ruby's gemspec has via `Boukensha::VERSION`. Worth
   a one-line reminder comment in the file itself, or accepted as a known
   manual step documented in the README instead.
4. **No verification-run cost concern this time** — unlike `05`-`08`,
   this step makes no API calls of its own; verification is installing
   the package and confirming `boukensha-py --help`-equivalent behavior
   (the resolve/debug-log/REPL-support-check paths) works, with an actual
   `boukensha-py` REPL session (pointed at live `08`) exercised the same
   way `08`'s own verification was — via short piped stdin, which *does*
   make real API calls, same as every REPL verification in this series.
