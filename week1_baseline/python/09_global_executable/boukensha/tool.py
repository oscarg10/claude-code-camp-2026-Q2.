from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    block: Callable

    def __str__(self):
        return f"#<Tool name={self.name} description={self.description[:41]} params={list(self.parameters.keys())}>"
