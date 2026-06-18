# 仕様: docs/spec/interface.md#post_user_reaction_controller
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from application.dtos.post_user_reaction_request import PostUserReactionRequest
from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.errors import InvalidRequest
from application.errors.use_case_errors import PostUserReactionError
from application.result import Result
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.time_range import TimeRange
from interface_adapters.events.user_reaction_submitted_event import (
    UserReactionSubmittedEvent,
)
from interface_adapters.outcomes.post_user_reaction_outcome import PostUserReactionOutcome
from interface_adapters.presentation.error_kind import error_kind_for

_USE_CASE = "post_user_reaction"


class AiReactionOrchestratorPort(Protocol):
    def on_user_reaction_posted(self, response: PostUserReactionResponse) -> None: ...


@dataclass(frozen=True, slots=True)
class PostUserReactionController:
    _use_case: Callable[
        [PostUserReactionRequest],
        Result[PostUserReactionResponse, PostUserReactionError],
    ]
    _orchestrator: AiReactionOrchestratorPort

    def execute(self, event: UserReactionSubmittedEvent) -> PostUserReactionOutcome:
        validation = self._validate_event(event)
        if validation is not None:
            return validation

        request = PostUserReactionRequest(
            lecture_id=event.lecture_id,
            reaction_text=ReactionText(text=event.reaction_text),
            lecture_time_anchor=LectureTimeAnchor.from_time_range(
                TimeRange(
                    start_ms=event.lecture_time_anchor_ms,
                    end_ms=event.lecture_time_anchor_ms,
                )
            ),
            speaker_display_name=event.speaker_display_name,
            reply_target=event.reply_target,
        )
        result = self._use_case(request)
        if result.is_err():
            return PostUserReactionOutcome(
                success=False,
                error_kind=error_kind_for(result.error),
            )

        response = result.value
        self._orchestrator.on_user_reaction_posted(response)
        return PostUserReactionOutcome(
            success=True,
            reaction_id=response.reaction_id,
            lecture_id=response.lecture_id,
        )

    def _validate_event(
        self, event: UserReactionSubmittedEvent
    ) -> PostUserReactionOutcome | None:
        if not event.lecture_id.strip():
            return PostUserReactionOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="lecture_id",
                        reason="lecture_id is required",
                    )
                ),
            )
        if not event.reaction_text.strip():
            return PostUserReactionOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="reaction_text",
                        reason="reaction_text is required",
                    )
                ),
            )
        if not event.speaker_display_name.strip():
            return PostUserReactionOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="speaker_display_name",
                        reason="speaker_display_name is required",
                    )
                ),
            )
        return None
