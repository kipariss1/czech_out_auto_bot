from typing import Any, Dict, defaultdict


class MockMessage:
    data: Dict[str, Any] = defaultdict(dict)
    text: str = ""

    def __init__(self, user_id, **kwargs):
        self.data["from_user"]["id"] = user_id
        self._add_text()

    def _add_text(self):
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
