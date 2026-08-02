from .agent import Agent
from .backends.anthropic import Anthropic
from .backends.gemini import Gemini
from .backends.ollama import Ollama
from .backends.ollama_cloud import OllamaCloud
from .backends.openai import OpenAI
from .client import Client
from .config import Config
from .context import Context
from .errors import ApiError, UnknownToolError, UnsupportedModelError
from .logger import Logger
from .message import Message
from .prompt_builder import PromptBuilder
from .registry import Registry
from .tasks.player import Player
from .tool import Tool

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


__all__ = [
    "Agent", "Anthropic", "Gemini", "Ollama", "OllamaCloud", "OpenAI", "Client",
    "Config", "Context", "ApiError", "UnknownToolError", "UnsupportedModelError",
    "Logger", "Message", "PromptBuilder", "Registry", "Player", "Tool",
    "config", "quiet", "loud", "is_quiet", "debug", "is_debug",
]
