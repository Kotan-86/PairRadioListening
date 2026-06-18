# 仕様: docs/spec/interface.md#refresh_transcript_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranscriptRefreshRequest:
    lecture_id: str
