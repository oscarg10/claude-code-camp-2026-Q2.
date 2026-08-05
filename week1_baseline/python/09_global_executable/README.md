# 09 · Global Executable (Python)

Package BOUKENSHA so the `boukensha-py` command works from anywhere on
your machine.

Unlike every step before it, this one adds no new capability to
`Boukensha` itself — `00`-`08` built up the library; this step just
packages what already exists behind one installable command.

## What this step adds

- `pyproject.toml` — declares the `boukensha-py` package: name, version,
  the `boukensha-py` console-script entry point
- `boukensha_loader.py` — resolves *which step folder* to load from, then
  boots the REPL
- `boukensha/` — a bundled copy of `08_the_repl_loop`'s package, used as
  the default when nothing else is configured

## Install

```bash
cd week1_baseline/python/09_global_executable
../../../.venv/bin/pip install -e .
```

(`pip install -e .`, not `pip install -r requirements.txt` — this step
needs the console-script entry point declared in `pyproject.toml`, which a
plain requirements file can't express. `requirements.txt` is still here
for consistency with every other step, but `pyproject.toml`'s own
`dependencies` already cover what's needed for this install.)

For `boukensha-py` to resolve from any directory, `<repo>/.venv/bin` needs
to be on `PATH` — add this to your shell rc file once:

```bash
export PATH="/path/to/claude-code-camp-2026-Q2./.venv/bin:$PATH"
```

## Switching steps with `BOUKENSHA_PY_PATH`

The loader resolves in this order:

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `BOUKENSHA_PY_PATH` env var | `BOUKENSHA_PY_PATH=~/Sites/boukensha/python/08_the_repl_loop boukensha-py` |
| 2 | `~/.boukensharc-py` file | `echo ~/Sites/boukensha/python/08_the_repl_loop > ~/.boukensharc-py` |
| 3 | Bundled default | just run `boukensha-py` |

`BOUKENSHA_PY_PATH` must point to a step folder that contains
`boukensha/__init__.py`.

**These names are deliberately distinct from Ruby's `BOUKENSHA_PATH` /
`~/.boukensharc`.** The Ruby `boukensha` command already uses those to
point at a Ruby step (`lib/boukensha.rb`); reusing them here would mean
whichever tool runs second either misreads a path meant for the other
language, or the two commands can't be pinned to different step numbers
at the same time. `BOUKENSHA_DIR` (the *config* directory —
`settings.yaml`, `.env`, prompt overrides) is shared between both
commands on purpose — the config format is language-agnostic, and both
tools reading the same `.boukensha/` avoids duplicating API keys and
settings. `BOUKENSHA_DEBUG` is shared too (same trigger, only the printed
prefix differs: `[boukensha-py]` vs `[boukensha]`).

## Recommended setup for this repo

Point `~/.boukensharc-py` at the live `08_the_repl_loop` folder, not the
bundled default, so `boukensha-py` reflects ongoing edits with no
reinstall step:

```bash
echo "/path/to/claude-code-camp-2026-Q2./week1_baseline/python/08_the_repl_loop" > ~/.boukensharc-py
```

This is the same reasoning already applied to the Ruby `boukensha`
command's `~/.boukensharc`.

## Running a specific step

```bash
# step 08 (interactive REPL)
BOUKENSHA_PY_PATH=~/Sites/boukensha/python/08_the_repl_loop boukensha-py

# step 07 doesn't have a REPL — loader tells you how to run it
BOUKENSHA_PY_PATH=~/Sites/boukensha/python/07_the_run_dsl boukensha-py
# => boukensha-py: the step at .../07_the_run_dsl does not support the interactive REPL
#    Run its examples directly, e.g.: python .../07_the_run_dsl/examples/example.py
```

## Debug mode

```bash
BOUKENSHA_DEBUG=1 boukensha-py
# => [boukensha-py] loading from: /path/to/step
```

## The Bundled Default Has Three Known Gaps vs. Live `08`

The `boukensha/` package shipped inside this folder is a **snapshot**, not
a live copy — and it was taken from a slightly earlier point than `08`'s
final state (mirroring the same gap in the Ruby gem's own bundled copy,
confirmed by diffing them directly). Running `boukensha-py` with no
override configured (tier 3, the bundled default) gets:

1. **No 401-specific error message** — an authentication failure surfaces
   the generic `"API request failed after N attempts (401): ..."` message
   rather than `"authentication failed (401) — check your API key"`.
2. **No CWD `.boukensha/` config tier** — config resolution is back to
   2-tier (`BOUKENSHA_DIR` → `~/.boukensha`), it won't pick up a
   `.boukensha/` in whatever directory you happen to run it from.
3. **A plainer banner** — no `✓ API key set` / `✗ API key not set`
   indicator, no "directory not found" warning if the config dir is
   missing; just bare `config:`/`provider:`/`model:` lines.

None of this affects the **recommended setup** above, since pointing
`~/.boukensharc-py` at live `08_the_repl_loop` bypasses the bundled
default entirely — these gaps only show up if you run `boukensha-py` with
zero configuration.

## Editable Install Means the Bundled Default Stays Live Too

Ruby's `gem build && gem install` copies files into a versioned archive —
picking up a code change means rebuilding and reinstalling. Python's
`pip install -e .` instead adds this directory itself to the interpreter's
import machinery, so even the *bundled default* stays live: editing
`boukensha/*.py` in this folder directly takes effect on the next
`boukensha-py` run, no reinstall needed. This is a real improvement over
the gem's frozen-snapshot model, not just a mechanical translation of it.

## The Key Idea

The package is just a **wrapper and a default**. All the teaching material
stays in the numbered step folders exactly as it was. Installing
`boukensha-py` doesn't copy or symlink any of them — the loader just knows
where to look, resolving to a real path on disk and loading that
specific `boukensha/__init__.py` via `importlib`, deterministically,
regardless of what else happens to be on the Python path.
