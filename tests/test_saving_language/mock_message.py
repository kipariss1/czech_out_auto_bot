from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MockMessage:
    data: Dict[str, Any] = field(default_factory=dict)
    text: str = field(default_factory=str)

    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.data["from_user"]["id"] = user_id
        self._add_text()

    def _add_text():
        self.data["text"] = self.text

    def __post_init__(self):
        for key, value in self.data.items():
            if isinstance(value, dict):
                object.__setattr__(self, key, DictToObject(value))
            else:
                object.__setattr__(self, key, value)

    def __getattr__(self, item):
        return self.data.get(item, None)


class StartMessage(MockMessage):
    text = "/start"


class LangMessage(MockMessage):
    text = "/RU"
