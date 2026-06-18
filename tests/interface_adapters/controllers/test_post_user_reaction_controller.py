# 仕様: docs/spec/interface.md#post_user_reaction_controller
from application.dtos.post_user_reaction_request import PostUserReactionRequest
from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.errors import TimelineNotEstablished
from application.result import Err, Ok
from domain.value_objects.reply_target import ReplyTarget
from interface_adapters.controllers.post_user_reaction_controller import (
    PostUserReactionController,
)
from interface_adapters.events.user_reaction_submitted_event import (
    UserReactionSubmittedEvent,
)
from tests.interface_adapters.conftest import SpyOrchestrator, StubUseCase


def test_post_user_reaction_controller_success_triggers_orchestrator():
    use_case = StubUseCase(
        result=Ok(
            PostUserReactionResponse(reaction_id="r-new", lecture_id="lecture-1")
        ),
    )
    orchestrator = SpyOrchestrator()
    controller = PostUserReactionController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )
    event = UserReactionSubmittedEvent(
        lecture_id="lecture-1",
        reaction_text="いいね",
        lecture_time_anchor_ms=5000,
        speaker_display_name="ユーザー",
        reply_target=ReplyTarget(reply_target_kind="reaction", reply_target_id="r0"),
    )

    outcome = controller.execute(event)

    assert len(use_case.requests) == 1
    request = use_case.requests[0]
    assert isinstance(request, PostUserReactionRequest)
    assert request.reply_target is not None
    assert outcome.success is True
    assert outcome.reaction_id == "r-new"
    assert len(orchestrator.user_reaction_posted) == 1


def test_post_user_reaction_controller_rejects_empty_text():
    use_case = StubUseCase(
        result=Ok(
            PostUserReactionResponse(reaction_id="r-new", lecture_id="lecture-1")
        ),
    )
    orchestrator = SpyOrchestrator()
    controller = PostUserReactionController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )

    outcome = controller.execute(
        UserReactionSubmittedEvent(
            lecture_id="lecture-1",
            reaction_text="  ",
            lecture_time_anchor_ms=0,
            speaker_display_name="ユーザー",
        )
    )

    assert use_case.requests == []
    assert orchestrator.user_reaction_posted == []
    assert outcome.success is False


def test_post_user_reaction_controller_does_not_call_orchestrator_on_failure():
    use_case = StubUseCase(
        result=Err(TimelineNotEstablished(lecture_id="lecture-1")),
    )
    orchestrator = SpyOrchestrator()
    controller = PostUserReactionController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )

    outcome = controller.execute(
        UserReactionSubmittedEvent(
            lecture_id="lecture-1",
            reaction_text="感想",
            lecture_time_anchor_ms=0,
            speaker_display_name="ユーザー",
        )
    )

    assert outcome.success is False
    assert outcome.error_kind == "timeline_not_established"
    assert orchestrator.user_reaction_posted == []
