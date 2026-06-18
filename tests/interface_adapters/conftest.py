# 仕様: docs/spec/interface.md#6 / §8
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from application.dtos.dialogue_item import DialogueItem, GetDialogueResponse
from application.dtos.transcript_item import GetTranscriptResponse, TranscriptItem
from application.result import Result
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")
TError = TypeVar("TError")
TViewModel = TypeVar("TViewModel")


@dataclass
class SpyViewModelStore(Generic[TViewModel, TError]):
    view_model: TViewModel | None = None
    last_error: TError | None = None
    present_count: int = 0
    present_error_count: int = 0

    def present(self, view_model: TViewModel) -> None:
        self.view_model = view_model
        self.present_count += 1

    def present_error(self, error: TError) -> None:
        self.last_error = error
        self.present_error_count += 1


@dataclass
class StubUseCase(Generic[TRequest, TResponse, TError]):
    result: Result[TResponse, TError]
    requests: list[TRequest] = field(default_factory=list)

    def execute(self, request: TRequest) -> Result[TResponse, TError]:
        self.requests.append(request)
        return self.result


@dataclass
class SpyOrchestrator:
    user_reaction_posted: list[Any] = field(default_factory=list)

    def on_user_reaction_posted(self, response: Any) -> None:
        self.user_reaction_posted.append(response)


@dataclass
class ImmediateTaskScheduler:
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


@dataclass
class SpyDialogueViewPort:
    refresh_calls: list[str] = field(default_factory=list)

    def refresh(self, request: Any) -> None:
        from interface_adapters.events.dialogue_refresh_request import (
            DialogueRefreshRequest,
        )

        if isinstance(request, DialogueRefreshRequest):
            self.refresh_calls.append(request.lecture_id)
            return
        lecture_id = getattr(request, "lecture_id", str(request))
        self.refresh_calls.append(str(lecture_id))


def make_transcript_item(
    *,
    utterance_id: str = "u1",
    start_ms: int = 0,
    end_ms: int = 1000,
    speech_text: str = "本文",
    speaker_name: str = "講師",
) -> TranscriptItem:
    return TranscriptItem(
        utterance_id=utterance_id,
        time_range=TimeRange(start_ms=start_ms, end_ms=end_ms),
        speech_text=SpeechText(text=speech_text),
        speaker=RecordingSpeaker(display_name=speaker_name),
    )


def make_get_transcript_response(
    *,
    lecture_id: str = "lecture-1",
    items: tuple[TranscriptItem, ...] | None = None,
) -> GetTranscriptResponse:
    if items is None:
        items = (make_transcript_item(),)
    return GetTranscriptResponse(lecture_id=lecture_id, items=items)


def make_dialogue_item(
    *,
    reaction_id: str = "r1",
    dialogue_sequence: int = 0,
    body: str = "感想",
    speaker_name: str = "ユーザー",
    speaker_role: str = "user",
    persona_id: str | None = None,
    reply_target_kind: str = "utterance",
    reply_target_id: str = "u1",
    start_ms: int = 0,
    end_ms: int = 1000,
) -> DialogueItem:
    speaker_kwargs: dict[str, Any] = {
        "role": speaker_role,
        "display_name": speaker_name,
    }
    if persona_id is not None:
        speaker_kwargs["persona_id"] = persona_id
    return DialogueItem(
        reaction_id=reaction_id,
        dialogue_sequence=dialogue_sequence,
        reaction_text=ReactionText(text=body),
        speaker=DialogueSpeaker(**speaker_kwargs),
        reply_target=ReplyTarget(
            reply_target_kind=reply_target_kind,
            reply_target_id=reply_target_id,
        ),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=start_ms, end_ms=end_ms)
        ),
    )


def make_get_dialogue_response(
    *,
    lecture_id: str = "lecture-1",
    items: tuple[DialogueItem, ...] | None = None,
) -> GetDialogueResponse:
    if items is None:
        items = (make_dialogue_item(),)
    return GetDialogueResponse(lecture_id=lecture_id, items=items)
