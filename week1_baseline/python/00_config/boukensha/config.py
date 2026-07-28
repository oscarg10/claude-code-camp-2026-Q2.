import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


class Config:
    # The .boukensha config directory is resolved in this order:
    #   1. BOUKENSHA_DIR environment variable (set before loading .env)
    #   2. ~/.boukensha  (default)
    DEFAULT_DIR = str(Path.home() / ".boukensha")

    # Default prompts shipped alongside the library code.
    PROMPTS_DIR = str(Path(__file__).resolve().parent.parent / "prompts")

    def __init__(self):
        self.dir = self._resolve_dir()
        self._load_env()
        self.settings = self._load_settings()

    # ---------- tasks -----------------------------------------------------

    # With no argument: returns the full tasks dict from settings.yaml.
    # With a name: returns that task's settings dict, e.g. tasks("player").
    def tasks(self, name=None):
        all_tasks = self.dig("tasks") or {}
        return all_tasks if name is None else all_tasks.get(str(name))

    # The user's prompts directory for task prompt overrides.
    @property
    def user_prompts_dir(self):
        return os.path.join(self.dir, "prompts")

    # ---------- MUD connection ---------------------------------------------

    @property
    def mud_host(self):
        return self.dig("mud", "host") or "localhost"

    @property
    def mud_port(self):
        return self.dig("mud", "port") or 4000

    @property
    def mud_username(self):
        return self.dig("mud", "username")

    @property
    def mud_password(self):
        return self.dig("mud", "password")

    # ---------- low-level helpers -------------------------------------------

    # Fetch a nested key path from settings, e.g. dig("mud", "host")
    def dig(self, *keys):
        node = self.settings
        for key in keys:
            if not isinstance(node, dict):
                return None
            node = node.get(str(key))
        return node

    def __str__(self):
        return f"#<Boukensha::Config dir={self.dir} tasks={','.join(self.tasks().keys())}>"

    __repr__ = __str__

    # ---------- internals ----------------------------------------------

    def _resolve_dir(self):
        raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
        return str(Path(raw).expanduser().resolve())

    def _load_env(self):
        env_file = os.path.join(self.dir, ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)

    def _load_settings(self):
        settings_file = os.path.join(self.dir, "settings.yaml")
        if os.path.exists(settings_file):
            with open(settings_file) as f:
                return yaml.safe_load(f) or {}
        return {}
