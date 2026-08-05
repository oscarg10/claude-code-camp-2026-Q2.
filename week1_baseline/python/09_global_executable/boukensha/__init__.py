import os

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
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .repl import Repl
from .run_dsl import RunDSL
from .tasks.player import Player
from .tool import Tool
from .version import VERSION

_state = {"quiet": False, "debug": False, "config": None}


def config():
    if _state["config"] is None:
        _state["config"] = Config()
    return _state["config"]


def quiet():
    _state["quiet"] = True


def loud():
    _state["quiet"] = False


def is_quiet():
    return _state["quiet"]


def debug():
    _state["debug"] = True


def is_debug():
    return _state["debug"]


def run(task, system=None, model=None, backend=None, api_key=None,
        ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    """The top-level entry point. Wires together every primitive so the
    caller only has to describe *what* to do, not *how* to plumb it.

        def register(dsl):
            dsl.tool("read_file",
                description="Read a file from disk",
                parameters={"path": {"type": "string", "description": "File path"}},
                block=lambda path: Path(path).read_text())

        result = boukensha.run(task="Summarise lib/boukensha.py", block=register)

    Args:
        task: (required) The user message to hand the agent.
        system: System prompt. Defaults to the player task's system prompt.
        model: Model name. Defaults to the player task's configured model.
        backend: "anthropic" (default from config), "openai", "gemini",
            "ollama", or "ollama_cloud".
        api_key: API key for the chosen backend. Defaults to the matching
            ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY /
            OLLAMA_API_KEY env var (loaded from .boukensha/.env). Not needed
            for "ollama".
        ollama_host: Ollama base URL. Defaults to "http://localhost:11434".
        log: Optional JSONL path override. Defaults to
            .boukensha/sessions/<session-id>.jsonl.
        max_output_tokens: Per-reply output cap. Defaults to the player
            task's configured value (1024).
        block: Optional callable invoked with a RunDSL instance, used to
            register tools: block(dsl) -> dsl.tool(...).
    """
    logger = None
    try:
        cfg = config()  # loads .env; populates os.environ
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())

        if system is None:
            system = task_class.system_prompt(
                task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=Config.PROMPTS_DIR
            )
        if model is None:
            model = task_class.model(task_settings)
        if backend is None:
            backend = task_class.provider(task_settings)
        if api_key is None:
            if backend == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif backend == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif backend == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY")
            elif backend == "ollama_cloud":
                api_key = os.environ.get("OLLAMA_API_KEY")

        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)

        if block is not None:
            block(RunDSL(registry))

        if backend == "anthropic":
            be = Anthropic(api_key=api_key, model=model)
        elif backend == "openai":
            be = OpenAI(api_key=api_key, model=model)
        elif backend == "gemini":
            be = Gemini(api_key=api_key, model=model)
        elif backend == "ollama":
            be = Ollama(host=ollama_host, model=model)
        elif backend == "ollama_cloud":
            be = OllamaCloud(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )

        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else task_class.max_output_tokens(task_settings)
        )
        logger = Logger(log=log, snapshot={
            "task": task_class.task_name(),
            "max_iterations": effective_max_iterations,
            "max_output_tokens": effective_max_output_tokens,
            "model": model,
            "provider": backend,
        })
        agent = Agent(
            context=ctx, registry=registry, builder=builder, client=client, logger=logger,
            task_settings=task_settings, max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
        )

        ctx.add_message("user", task)
        return agent.run()
    finally:
        if logger is not None:
            logger.close()


def repl(system=None, model=None, backend=None, api_key=None,
         ollama_host="http://localhost:11434", log=None, max_output_tokens=None, block=None):
    """Interactive REPL: register tools once, then loop — reading tasks
    from stdin, running the agent, and printing replies — until the user
    types /exit or sends EOF.

    Conversation history accumulates across every turn so the agent always
    sees the full transcript.

    Same arguments as run(), minus `task` (the user supplies tasks
    interactively).
    """
    logger = None
    try:
        cfg = config()  # loads .env; populates os.environ
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())

        if system is None:
            system = task_class.system_prompt(
                task_settings, user_prompts_dir=cfg.user_prompts_dir, default_prompts_dir=Config.PROMPTS_DIR
            )
        if model is None:
            model = task_class.model(task_settings)
        if backend is None:
            backend = task_class.provider(task_settings)
        if api_key is None:
            if backend == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif backend == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
            elif backend == "gemini":
                api_key = os.environ.get("GEMINI_API_KEY")
            elif backend == "ollama_cloud":
                api_key = os.environ.get("OLLAMA_API_KEY")

        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)

        if block is not None:
            block(RunDSL(registry))

        if backend == "anthropic":
            be = Anthropic(api_key=api_key, model=model)
        elif backend == "openai":
            be = OpenAI(api_key=api_key, model=model)
        elif backend == "gemini":
            be = Gemini(api_key=api_key, model=model)
        elif backend == "ollama":
            be = Ollama(host=ollama_host, model=model)
        elif backend == "ollama_cloud":
            be = OllamaCloud(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )

        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else task_class.max_output_tokens(task_settings)
        )
        logger = Logger(log=log, snapshot={
            "task": task_class.task_name(),
            "max_iterations": effective_max_iterations,
            "max_output_tokens": effective_max_output_tokens,
            "model": model,
            "provider": backend,
        })

        Repl(
            context=ctx, registry=registry, builder=builder, client=client, logger=logger,
            task_settings=task_settings, max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens, config_dir=cfg.dir,
            provider=backend, model=model, version=VERSION, api_key=api_key,
        ).start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger is not None:
            logger.close()


__all__ = [
    "Agent", "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "LoopError", "UnknownToolError", "UnsupportedModelError",
    "Logger", "Message", "PromptBuilder", "Registry", "Repl", "RunDSL", "Player", "Tool",
    "VERSION", "config", "quiet", "loud", "is_quiet", "debug", "is_debug", "run", "repl",
]
