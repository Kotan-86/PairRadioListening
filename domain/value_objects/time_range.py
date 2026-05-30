# 仕様: docs/spec/domain.md#time_range
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeRange:
    start_ms: int
    end_ms: int

    def __post_init__(self):
        if self.start_ms < 0 or self.end_ms < 0:
            raise ValueError("講義タイムライン上の時間は0ミリ秒である必要があります")
        if self.start_ms > self.end_ms:
            raise ValueError("講義タイムライン上の時間は開始時刻が終了時刻よりも前になることはありません")
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
