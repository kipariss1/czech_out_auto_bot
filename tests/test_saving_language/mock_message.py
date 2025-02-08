from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Message:
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        for key, value in self.data.items():
            if isinstance(value, dict):
                object.__setattr__(self, key, DictToObject(value))
            else:
                object.__setattr__(self, key, value)

    def __getattr__(self, item):
        return self.data.get(item, None)
