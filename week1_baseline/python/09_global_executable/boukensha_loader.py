"""Resolves which step folder to load boukensha from, then boots the REPL.

Resolution order:
  1. BOUKENSHA_PY_PATH environment variable (selects which *step* package to load)
  2. ~/.boukensharc-py  (a file containing a single path)
  3. The boukensha/ directory bundled inside this package (the latest release)

Config directory (settings.yaml, .env, prompts) is separate, and shared
with the Ruby boukensha command on purpose:
  BOUKENSHA_DIR=~/.boukensha  (default, set in env to override)

Examples:
  boukensha-py                                                                      # uses bundled default + ~/.boukensha
  BOUKENSHA_PY_PATH=~/Sites/boukensha/python/08_the_repl_loop boukensha-py          # loads step 08
  BOUKENSHA_DIR=~/projects/mybot/.boukensha boukensha-py                           # custom config dir
  echo ~/Sites/boukensha/python/08_the_repl_loop > ~/.boukensharc-py && boukensha-py # permanent step default
"""

import importlib.util
import os
import sys
from pathlib import Path

# Absolute path to this file's own directory — the bundled default lives in
# a boukensha/ package right next to it, the direct analogue of Ruby's
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
