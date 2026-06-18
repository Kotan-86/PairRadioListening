# 仕様: docs/spec/framework.md#2.3, #4
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.reply_target import ReplyTarget
from framework.http.error_mapping import http_status_for_command, http_status_for_start
from framework.http.schemas import (
    DialogueViewModelSchema,
    EndLectureOutcomeSchema,
    HealthResponse,
    PostUserReactionOutcomeSchema,
    PostUserReactionRequestBody,
    RecordUtteranceOutcomeSchema,
    RecordUtteranceRequestBody,
    StartLectureOutcomeSchema,
    StartLectureRequestBody,
    TranscriptViewModelSchema,
)
from interface_adapters.events.dialogue_refresh_request import DialogueRefreshRequest
from interface_adapters.events.end_lecture_session_event import EndLectureSessionEvent
from interface_adapters.events.speech_recognition_utterance_event import (
    SpeechRecognitionUtteranceEvent,
)
from interface_adapters.events.start_lecture_form_event import StartLectureFormEvent
from interface_adapters.events.transcript_refresh_request import TranscriptRefreshRequest
from interface_adapters.events.user_reaction_submitted_event import UserReactionSubmittedEvent

if TYPE_CHECKING:
    from framework.bootstrap import AppDeps


def create_http_router(deps: AppDeps) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @router.post("/api/lectures/start")
    def start_lecture(body: StartLectureRequestBody) -> JSONResponse:
        # 仕様: docs/spec/interface.md#start_lecture_controller
        profiles = tuple(
            AiPersonaProfile(
                id=profile.id,
                display_name=profile.display_name,
                persona_prompt=profile.persona_prompt,
            )
            for profile in body.persona_profiles
        )
        event = StartLectureFormEvent(persona_profiles=profiles, title=body.title)
        outcome = deps.start_lecture.execute(event)
        status = http_status_for_start(
            success=outcome.success,
            error_kind=outcome.error_kind,
        )
        payload = StartLectureOutcomeSchema.from_outcome(outcome).model_dump()
        return JSONResponse(status_code=status, content=payload)

    @router.post("/api/lectures/{lecture_id}/end")
    def end_lecture(lecture_id: str) -> JSONResponse:
        # 仕様: docs/spec/interface.md#end_lecture_controller
        outcome = deps.end_lecture.execute(EndLectureSessionEvent(lecture_id=lecture_id))
        status = http_status_for_command(
            success=outcome.success,
            error_kind=outcome.error_kind,
        )
        payload = EndLectureOutcomeSchema.from_outcome(outcome).model_dump()
        return JSONResponse(status_code=status, content=payload)

    @router.post("/api/lectures/{lecture_id}/reactions")
    def post_reaction(lecture_id: str, body: PostUserReactionRequestBody) -> JSONResponse:
        # 仕様: docs/spec/interface.md#post_user_reaction_controller
        reply_target = _parse_reply_target(body.reply_target)
        event = UserReactionSubmittedEvent(
            lecture_id=lecture_id,
            reaction_text=body.reaction_text,
            lecture_time_anchor_ms=body.lecture_time_anchor,
            speaker_display_name=body.speaker_display_name,
            reply_target=reply_target,
        )
        outcome = deps.post_user_reaction.execute(event)
        status = http_status_for_command(
            success=outcome.success,
            error_kind=outcome.error_kind,
        )
        payload = PostUserReactionOutcomeSchema.from_outcome(outcome).model_dump()
        return JSONResponse(status_code=status, content=payload)

    @router.get("/api/lectures/{lecture_id}/transcript")
    def get_transcript(lecture_id: str) -> TranscriptViewModelSchema:
        # 仕様: docs/spec/interface.md#refresh_transcript_controller
        deps.refresh_transcript.execute(TranscriptRefreshRequest(lecture_id=lecture_id))
        view_model = deps.transcript_store.get(lecture_id)
        if view_model is None:
            return TranscriptViewModelSchema(
                lecture_id=lecture_id,
                lines=[],
                error_message="transcript is not available",
            )
        return TranscriptViewModelSchema.from_view_model(view_model)

    @router.get("/api/lectures/{lecture_id}/dialogue")
    def get_dialogue(lecture_id: str) -> DialogueViewModelSchema:
        # 仕様: docs/spec/interface.md#refresh_dialogue_controller
        deps.refresh_dialogue.execute(DialogueRefreshRequest(lecture_id=lecture_id))
        view_model = deps.dialogue_store.get(lecture_id)
        if view_model is None:
            return DialogueViewModelSchema(
                lecture_id=lecture_id,
                lines=[],
                error_message="dialogue is not available",
            )
        return DialogueViewModelSchema.from_view_model(view_model)

    @router.post("/internal/amivoice/utterances")
    def record_utterance(body: RecordUtteranceRequestBody) -> JSONResponse:
        # 仕様: docs/spec/interface.md#record_utterance_controller
        event = SpeechRecognitionUtteranceEvent(
            lecture_id=body.lecture_id,
            utterance_id=body.utterance_id,
            start_ms=body.start_ms,
            end_ms=body.end_ms,
            transcript=body.speech_text,
            speaker_display_name=body.speaker_display_name,
        )
        outcome = deps.record_utterance.execute(event)
        status = http_status_for_command(
            success=outcome.success,
            error_kind=outcome.error_kind,
        )
        payload = RecordUtteranceOutcomeSchema.from_outcome(outcome).model_dump()
        return JSONResponse(status_code=status, content=payload)

    return router


def _parse_reply_target(raw: dict[str, str] | None) -> ReplyTarget | None:
    if raw is None:
        return None
    kind = raw.get("reply_target_kind", "")
    target_id = raw.get("reply_target_id", "")
    if not kind or not target_id:
        return None
    return ReplyTarget(reply_target_kind=kind, reply_target_id=target_id)
