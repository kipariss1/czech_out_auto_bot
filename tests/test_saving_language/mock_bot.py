from typing import Callable, Dict
from unittest.mock import MagicMock


class MockBot(MagicMock):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._callable_list = []
        self._results = []

    def add_handler(new_handler: Callable, kwargs: Dict):
        self._callable_list.append({"func": new_handler, "kwargs": kwargs})

    def infinity_polling():
        for f in self._callable_list:
            self._results.append(f["func"](**f["kwargs"]))

    def get_result(idx: int):
        return self._results[idx]
