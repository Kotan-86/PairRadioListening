# 仕様: docs/spec/framework_llm.md#5.2
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


class LlmRateLimitExceeded(RuntimeError):
    """RPM / RPD 上限により LLM 呼び出しを拒否した。"""


@dataclass
class LlmRateLimiter:
    rpm_limit: int
    rpd_limit: int
    _minute_timestamps: deque[float] = field(default_factory=deque)
    _day_timestamps: deque[float] = field(default_factory=deque)

    def acquire(self) -> None:
        now = time.monotonic()
        self._prune(now)
        if len(self._minute_timestamps) >= self.rpm_limit:
            raise LlmRateLimitExceeded("RPM limit exceeded")
        if len(self._day_timestamps) >= self.rpd_limit:
            raise LlmRateLimitExceeded("RPD limit exceeded")
        self._minute_timestamps.append(now)
        self._day_timestamps.append(now)

    def _prune(self, now: float) -> None:
        minute_cutoff = now - 60.0
        while self._minute_timestamps and self._minute_timestamps[0] < minute_cutoff:
            self._minute_timestamps.popleft()

        day_cutoff = now - 86_400.0
        while self._day_timestamps and self._day_timestamps[0] < day_cutoff:
            self._day_timestamps.popleft()
