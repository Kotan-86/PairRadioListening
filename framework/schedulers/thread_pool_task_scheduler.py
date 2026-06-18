# 仕様: docs/spec/framework.md#6.3, docs/spec/framework_llm.md#2
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from interface_adapters.ports.background_task_port import BackgroundTaskPort


@dataclass
class ThreadPoolTaskScheduler(BackgroundTaskPort):
    """MVP: AI 生成を直列化する単一ワーカーの非同期スケジューラ。"""

    max_workers: int = 1
    _executor: ThreadPoolExecutor = field(init=False, repr=False)
    scheduled: list[Callable[[], None]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="ai-task",
        )

    def schedule(self, task: Callable[[], None]) -> None:
        self.scheduled.append(task)
        self._executor.submit(task)

    def shutdown(self, *, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)
