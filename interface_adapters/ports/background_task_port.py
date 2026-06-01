# 仕様: docs/spec/interface.md#8.2
from collections.abc import Callable
from typing import Protocol


class BackgroundTaskPort(Protocol):
    def schedule(self, task: Callable[[], None]) -> None: ...
