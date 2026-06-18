# 仕様: docs/spec/framework.md#3, docs/spec/interface.md#3.3 / §7
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from interface_adapters.outcomes.end_lecture_outcome import EndLectureOutcome
from interface_adapters.outcomes.post_user_reaction_outcome import PostUserReactionOutcome
from interface_adapters.outcomes.record_utterance_outcome import RecordUtteranceOutcome
from interface_adapters.outcomes.start_lecture_outcome import StartLectureOutcome
from interface_adapters.view_models.dialogue_view_model import (
    DialogueLineView,
    DialogueViewModel,
)
from interface_adapters.view_models.transcript_view_model import (
    TranscriptLineView,
    TranscriptViewModel,
)


class _SnakeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(_SnakeModel):
    status: str


class StartLectureOutcomeSchema(_SnakeModel):
    success: bool
    lecture_id: str = ""
    error_kind: str = ""

    @classmethod
    def from_outcome(cls, outcome: StartLectureOutcome) -> StartLectureOutcomeSchema:
        return cls(
            success=outcome.success,
            lecture_id=outcome.lecture_id,
            error_kind=outcome.error_kind,
        )


class EndLectureOutcomeSchema(_SnakeModel):
    success: bool
    lecture_id: str = ""
    ended_at: int = 0
    error_kind: str = ""

    @classmethod
    def from_outcome(cls, outcome: EndLectureOutcome) -> EndLectureOutcomeSchema:
        return cls(
            success=outcome.success,
            lecture_id=outcome.lecture_id,
            ended_at=outcome.ended_at,
            error_kind=outcome.error_kind,
        )


class PostUserReactionOutcomeSchema(_SnakeModel):
    success: bool
    reaction_id: str = ""
    lecture_id: str = ""
    error_kind: str = ""

    @classmethod
    def from_outcome(cls, outcome: PostUserReactionOutcome) -> PostUserReactionOutcomeSchema:
        return cls(
            success=outcome.success,
            reaction_id=outcome.reaction_id,
            lecture_id=outcome.lecture_id,
            error_kind=outcome.error_kind,
        )


class RecordUtteranceOutcomeSchema(_SnakeModel):
    success: bool
    utterance_id: str = ""
    lecture_id: str = ""
    error_kind: str = ""

    @classmethod
    def from_outcome(cls, outcome: RecordUtteranceOutcome) -> RecordUtteranceOutcomeSchema:
        return cls(
            success=outcome.success,
            utterance_id=outcome.utterance_id,
            lecture_id=outcome.lecture_id,
            error_kind=outcome.error_kind,
        )


class TranscriptLineSchema(_SnakeModel):
    utterance_id: str
    time_label: str
    speaker_label: str
    body: str


class TranscriptViewModelSchema(_SnakeModel):
    lecture_id: str
    lines: list[TranscriptLineSchema]
    error_message: str

    @classmethod
    def from_view_model(cls, view_model: TranscriptViewModel) -> TranscriptViewModelSchema:
        return cls(
            lecture_id=view_model.lecture_id,
            lines=[_transcript_line(line) for line in view_model.lines],
            error_message=view_model.error_message,
        )


class DialogueLineSchema(_SnakeModel):
    reaction_id: str
    speaker_label: str
    body: str
    reference_time_label: str
    reference_quote_label: str


class DialogueViewModelSchema(_SnakeModel):
    lecture_id: str
    lines: list[DialogueLineSchema]
    error_message: str

    @classmethod
    def from_view_model(cls, view_model: DialogueViewModel) -> DialogueViewModelSchema:
        return cls(
            lecture_id=view_model.lecture_id,
            lines=[_dialogue_line(line) for line in view_model.lines],
            error_message=view_model.error_message,
        )


class PersonaProfileBody(_SnakeModel):
    id: str
    display_name: str
    persona_prompt: str = ""


class StartLectureRequestBody(_SnakeModel):
    persona_profiles: list[PersonaProfileBody] = Field(min_length=1)
    title: str = ""


class PostUserReactionRequestBody(_SnakeModel):
    reaction_text: str
    lecture_time_anchor: int
    speaker_display_name: str
    reply_target: dict[str, str] | None = None


class RecordUtteranceRequestBody(_SnakeModel):
    lecture_id: str
    utterance_id: str
    speech_text: str
    speaker_display_name: str
    start_ms: int
    end_ms: int


def _transcript_line(line: TranscriptLineView) -> TranscriptLineSchema:
    return TranscriptLineSchema(
        utterance_id=line.utterance_id,
        time_label=line.time_label,
        speaker_label=line.speaker_label,
        body=line.body,
    )


def _dialogue_line(line: DialogueLineView) -> DialogueLineSchema:
    return DialogueLineSchema(
        reaction_id=line.reaction_id,
        speaker_label=line.speaker_label,
        body=line.body,
        reference_time_label=line.reference_time_label,
        reference_quote_label=line.reference_quote_label,
    )
