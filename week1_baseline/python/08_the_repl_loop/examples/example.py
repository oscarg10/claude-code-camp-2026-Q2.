import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boukensha

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically (or,
# since this step, any .boukensha/ found in the current working directory).
os.environ.setdefault("BOUKENSHA_DIR", str(Path(__file__).resolve().parents[4] / ".boukensha"))

print(f"Config: {boukensha.config()}")
print()

# The base directory tools will operate relative to — 07_the_run_dsl makes
# a good playground since it already has source files to read.
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "07_the_run_dsl"


def register(dsl):
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "File path (relative to the working directory)"}},
        block=lambda path: Path(BASE_DIR, path).read_text(),
    )
    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "Directory path (relative to the working directory, or '.' for root)"}},
        block=lambda path: ", ".join(
            sorted(entry for entry in os.listdir(Path(BASE_DIR, path)) if not entry.startswith("."))
        ),
    )


boukensha.repl(block=register)
