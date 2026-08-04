import os
import sys

import boukensha

from .agent import Agent
from .errors import ApiError, LoopError


class Repl:
    """The interactive session loop.

    Wraps the same primitives as a single boukensha.run() call, but instead
    of running once it stays alive: it reads a task from the user, runs the
    agent, prints the reply, and loops back to the prompt.

    The Context is shared across every turn so conversation history
    accumulates naturally — the agent sees the full transcript each time
    it is called.
    """

    PROMPT = "boukensha> "
    HELP = (
        "Commands:\n"
        "  /quiet   suppress logging output\n"
        "  /loud    re-enable logging output\n"
        "  /clear   wipe conversation history (tools stay)\n"
        "  /exit    leave the REPL\n"
        "  /help    show this message"
    )

    def __init__(self, context, registry, builder, client, logger, config_dir=None,
                 provider=None, model=None, version=None, api_key=None,
                 task_settings=None, max_iterations=None, max_output_tokens=None):
        self.context = context
        self.registry = registry
        self.builder = builder
        self.client = client
        self.logger = logger
        self.task_settings = task_settings
        self.max_iterations = max_iterations
        self.max_output_tokens = max_output_tokens
        self.config_dir = config_dir
        self.provider = provider
        self.model = model
        self.version = version
        self.api_key = api_key
        self.turn = 0

    def start(self):
        print(self._banner(), end="")

        while True:
            sys.stdout.write(self.PROMPT)
            sys.stdout.flush()

            line = sys.stdin.readline()
            if not line:
                break  # EOF / Ctrl-D

            user_input = line.strip()
            if not user_input:
                continue

            if user_input in ("/exit", "/quit"):
                print("Goodbye.")
                break
            elif user_input == "/help":
                print(self.HELP)
                continue
            elif user_input == "/quiet":
                boukensha.quiet()
                print("(logging suppressed — type /loud to re-enable)")
                continue
            elif user_input == "/loud":
                boukensha.loud()
                print("(logging enabled)")
                continue
            elif user_input == "/clear":
                self.context.clear_messages()
                self.turn = 0
                print("(conversation history cleared)")
                continue

            self._run_turn(user_input)

    def _banner(self):
        if self.api_key is None or not self.api_key.strip():
            key_status = "✗ API key not set"
        else:
            key_status = "✓ API key set"
        provider_line = f"{self.provider or 'default'} ({self.model or 'default'})  {key_status}"
        config_exists = bool(self.config_dir) and os.path.isdir(self.config_dir)
        config_line = self.config_dir if config_exists else f"{self.config_dir or '(default)'}  ✗ directory not found"
        ver = self.version or "?.?.?"
        padding = " " * (9 - len(ver))

        return (
            "\n"
            "╔══════════════════════════════════════╗\n"
            f"║  BOUKENSHA MUD Assistant (v{ver}){padding}║\n"
            "╚══════════════════════════════════════╝\n"
            f"  config:    {config_line}\n"
            f"  provider:  {provider_line}\n"
            "\n"
            "  /quiet or /loud   toggle logging\n"
            "  /clear           reset conversation history\n"
            "  /exit or /quit    leave the REPL\n"
            "\n"
        )

    def _run_turn(self, user_input):
        try:
            self.turn += 1
            self.logger.turn(n=self.turn)

            self.context.add_message("user", user_input)

            agent = Agent(
                context=self.context, registry=self.registry, builder=self.builder,
                client=self.client, logger=self.logger, task_settings=self.task_settings,
                max_iterations=self.max_iterations, max_output_tokens=self.max_output_tokens,
            )
            result = agent.run()

            # Print the final response outside of the logger so it is
            # always visible, even when boukensha.quiet() is active.
            print()
            print(result)
        except LoopError as e:
            print(f"\n[error] {e}")
        except ApiError as e:
            print(f"\n[error] API call failed: {e}")
