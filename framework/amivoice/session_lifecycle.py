# 仕様: docs/spec/framework_amivoice.md#4.2
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from interface_adapters.events.end_lecture_session_event import EndLectureSessionEvent
from interface_adapters.events.start_lecture_form_event import StartLectureFormEvent
from interface_adapters.outcomes.end_lecture_outcome import EndLectureOutcome
from interface_adapters.outcomes.start_lecture_outcome import StartLectureOutcome


@dataclass(frozen=True, slots=True)
class BridgeAwareStartLectureController:
    _inner: Callable[[StartLectureFormEvent], StartLectureOutcome]
    _on_started: Callable[[str], None]

    def execute(self, event: StartLectureFormEvent) -> StartLectureOutcome:
        outcome = self._inner(event)
        if outcome.success:
            self._on_started(outcome.lecture_id)
        return outcome


@dataclass(frozen=True, slots=True)
class BridgeAwareEndLectureController:
    _inner: Callable[[EndLectureSessionEvent], EndLectureOutcome]
    _on_ended: Callable[[str], None]

    def execute(self, event: EndLectureSessionEvent) -> EndLectureOutcome:
        # 講義クローズ前に Bridge を終了し、最終 AmiVoice 区間を record_utterance 可能にする。
        self._on_ended(event.lecture_id)
        return self._inner(event)
