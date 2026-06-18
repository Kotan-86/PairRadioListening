# 仕様: docs/spec/interface.md#6.4 / §6.5
from domain.value_objects.time_range import TimeRange

TIME_LABEL_RANGE_SEPARATOR = "–"


def _ms_to_clock_label(ms: int) -> str:
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def format_time_label(time_range: TimeRange) -> str:
    start = _ms_to_clock_label(time_range.start_ms)
    end = _ms_to_clock_label(time_range.end_ms)
    return f"{start}{TIME_LABEL_RANGE_SEPARATOR}{end}"
