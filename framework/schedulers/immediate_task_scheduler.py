# 仕様: docs/spec/framework.md#6.3, docs/spec/interface.md#8
from collections.abc import Callable
from dataclasses import dataclass, field

from interface_adapters.ports.background_task_port import BackgroundTaskPort


@dataclass
class ImmediateTaskScheduler(BackgroundTaskPort):
    """MVP テスト・Phase0 用の同期スケジューラ（`interface_adapters` テストと同型）。"""

    defer: bool = False
    scheduled: list[Callable[[], None]] = field(default_factory=list)

    def schedule(self, task: Callable[[], None]) -> None:
        if self.defer:
            self.scheduled.append(task)
            return
        task()

    def flush(self) -> None:
        for task in self.scheduled:
            task()
        self.scheduled.clear()
