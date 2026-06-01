# 仕様: docs/spec/interface.md#refresh_transcript_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranscriptRefreshOutcome:
    success: bool
    item_count: int = 0
    error_kind: str = ""
