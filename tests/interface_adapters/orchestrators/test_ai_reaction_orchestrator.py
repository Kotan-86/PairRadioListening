# 仕様: docs/spec/interface.md#8.3, docs/spec/framework_llm.md#2
from dataclasses import dataclass, field

from application.dtos.generate_ai_replies_for_user_reaction_request import (
    GenerateAiRepliesForUserReactionRequest,
)
from application.dtos.generate_ai_replies_for_user_reaction_response import (
    GenerateAiRepliesForUserReactionResponse,
)
from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.errors import AiTextGenerationFailed
from application.result import Err, Ok
from interface_adapters.orchestrators.ai_reaction_orchestrator import AiReactionOrchestrator
from tests.interface_adapters.conftest import ImmediateTaskScheduler, SpyDialogueViewPort


@dataclass
class SpyGenerateUseCase:
    requests: list = field(default_factory=list)
    result: object = None

    def __post_init__(self):
        if self.result is None:
            self.result = Ok(
                GenerateAiRepliesForUserReactionResponse(
                    lecture_id="lecture-1",
                    user_reaction_id="r-user",
                    reaction_id="r-ai",
                )
            )

    def execute(self, request):
        self.requests.append(request)
        return self.result


def test_on_user_reaction_posted_schedules_generate_use_case():
    reaction_uc = SpyGenerateUseCase()
    view_port = SpyDialogueViewPort()
    orchestrator = AiReactionOrchestrator(
        _generate_for_user_reaction_use_case=reaction_uc.execute,
        _dialogue_view_port=view_port,
        _task_scheduler=ImmediateTaskScheduler(),
    )

    orchestrator.on_user_reaction_posted(
        PostUserReactionResponse(reaction_id="r-user", lecture_id="lecture-1")
    )

    assert len(reaction_uc.requests) == 1
    request = reaction_uc.requests[0]
    assert isinstance(request, GenerateAiRepliesForUserReactionRequest)
    assert request.reaction_id == "r-user"
    assert view_port.refresh_calls == ["lecture-1"]


def test_on_user_reaction_posted_does_not_refresh_on_use_case_error():
    reaction_uc = SpyGenerateUseCase(
        result=Err(
            AiTextGenerationFailed(
                lecture_id="lecture-1",
                trigger="user_reaction",
                source_id="r-user",
            )
        )
    )
    view_port = SpyDialogueViewPort()
    orchestrator = AiReactionOrchestrator(
        _generate_for_user_reaction_use_case=reaction_uc.execute,
        _dialogue_view_port=view_port,
        _task_scheduler=ImmediateTaskScheduler(),
    )

    orchestrator.on_user_reaction_posted(
        PostUserReactionResponse(reaction_id="r-user", lecture_id="lecture-1")
    )

    assert view_port.refresh_calls == []


def test_orchestrator_deferred_schedule_does_not_block_until_flush():
    reaction_uc = SpyGenerateUseCase()
    scheduler = ImmediateTaskScheduler(defer=True)
    view_port = SpyDialogueViewPort()
    orchestrator = AiReactionOrchestrator(
        _generate_for_user_reaction_use_case=reaction_uc.execute,
        _dialogue_view_port=view_port,
        _task_scheduler=scheduler,
    )

    orchestrator.on_user_reaction_posted(
        PostUserReactionResponse(reaction_id="r-user", lecture_id="lecture-1")
    )

    assert reaction_uc.requests == []
    assert view_port.refresh_calls == []

    scheduler.flush()

    assert len(reaction_uc.requests) == 1
    assert view_port.refresh_calls == ["lecture-1"]
