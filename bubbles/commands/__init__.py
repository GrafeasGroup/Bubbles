from dataclasses import dataclass, asdict
from typing import Callable


@dataclass
class Plugin:
    callable: Callable
    regex: str
    flags: int = None
    callback: Callable = None
    ignore_prefix: bool = False
    help: str = None
    interactive_friendly: bool = True

    def to_dict(self):
        return asdict(self)
