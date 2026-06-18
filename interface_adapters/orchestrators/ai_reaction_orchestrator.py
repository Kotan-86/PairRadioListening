# 仕様: docs/spec/interface.md#8.2, docs/spec/framework_llm.md#2
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from application.dtos.generate_ai_replies_for_user_reaction_request import (
    GenerateAiRepliesForUserReactionRequest,
)
from application.dtos.generate_ai_replies_for_user_reaction_response import (
    GenerateAiRepliesForUserReactionResponse,
)
from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.errors.use_case_errors import GenerateAiRepliesForUserReactionError
from application.result import Result
from interface_adapters.events.dialogue_refresh_request import DialogueRefreshRequest
from interface_adapters.ports.background_task_port import BackgroundTaskPort


class DialogueViewPort(Protocol):
    def refresh(self, request: DialogueRefreshRequest) -> Any: ...


@dataclass(frozen=True, slots=True)
class AiReactionOrchestrator:
    _generate_for_user_reaction_use_case: Callable[
        [GenerateAiRepliesForUserReactionRequest],
        Result[
            GenerateAiRepliesForUserReactionResponse,
            GenerateAiRepliesForUserReactionError,
        ],
    ]
    _dialogue_view_port: DialogueViewPort
    _task_scheduler: BackgroundTaskPort

    def on_user_reaction_posted(self, response: PostUserReactionResponse) -> None:
        request = GenerateAiRepliesForUserReactionRequest(
            lecture_id=response.lecture_id,
            reaction_id=response.reaction_id,
        )
        self._task_scheduler.schedule(
            lambda: self._run_generate_for_user_reaction(request, response.lecture_id)
        )

    def _run_generate_for_user_reaction(
        self,
        request: GenerateAiRepliesForUserReactionRequest,
        lecture_id: str,
    ) -> None:
        result = self._generate_for_user_reaction_use_case(request)
        if result.is_ok():
            self._dialogue_view_port.refresh(DialogueRefreshRequest(lecture_id=lecture_id))
