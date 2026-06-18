# 仕様: docs/spec/framework.md#5
from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.use_cases.end_lecture_use_case import EndLectureUseCase
from application.use_cases.get_dialogue_use_case import GetDialogueUseCase
from application.use_cases.get_transcript_use_case import GetTranscriptUseCase
from application.use_cases.post_user_reaction_use_case import PostUserReactionUseCase
from application.use_cases.record_utterance_use_case import RecordUtteranceUseCase
from application.use_cases.start_lecture_use_case import StartLectureUseCase
from application.errors.use_case_errors import GetDialogueError, GetTranscriptError
from infrastructure.repositories import InMemoryLectureRepository, InMemoryReactionRepository
from interface_adapters.controllers.end_lecture_controller import EndLectureController
from interface_adapters.controllers.post_user_reaction_controller import (
    PostUserReactionController,
)
from interface_adapters.controllers.record_utterance_controller import RecordUtteranceController
from interface_adapters.controllers.refresh_dialogue_controller import RefreshDialogueController
from interface_adapters.controllers.refresh_transcript_controller import (
    RefreshTranscriptController,
)
from interface_adapters.controllers.start_lecture_controller import StartLectureController
from framework.amivoice.amivoice_streaming_bridge import AmiVoiceStreamingBridge
from framework.amivoice.audio_capture_source import (
    AudioCaptureSource,
    SoundDeviceAudioCaptureSource,
)
from framework.amivoice.session_commands import amivoice_start_command
from framework.amivoice.wrp_session import WrpAmiVoiceSessionFactory
from framework.amivoice.null_ws_session import NullAmiVoiceWsSessionFactory
from framework.amivoice.ws_session import AmiVoiceWsSessionFactory
from framework.amivoice.session_lifecycle import (
    BridgeAwareEndLectureController,
    BridgeAwareStartLectureController,
)
from interface_adapters.mappers.dialogue_view_model_mapper import DialogueViewModelMapper
from interface_adapters.mappers.transcript_view_model_mapper import TranscriptViewModelMapper
from interface_adapters.presenters.dialogue_presenter import DialoguePresenter
from interface_adapters.presenters.transcript_presenter import TranscriptPresenter
from interface_adapters.view_models.dialogue_view_model import DialogueViewModel
from interface_adapters.view_models.transcript_view_model import TranscriptViewModel
from framework.http.router import create_http_router
from framework.schedulers.immediate_task_scheduler import ImmediateTaskScheduler
from framework.logging_config import configure_logging
from framework.settings import Settings, load_settings
from framework.stores.lecture_view_model_store import LectureViewModelStore

logger = logging.getLogger(__name__)


@dataclass
class NoOpAiReactionOrchestrator:
    """Phase0–2: LLM 未配線時に AI 生成を起動しない。"""

    call_count: int = 0

    def on_user_reaction_posted(self, response: PostUserReactionResponse) -> None:
        _ = response
        self.call_count += 1


@dataclass(frozen=True, slots=True)
class AppDeps:
    settings: Settings
    lecture_repository: InMemoryLectureRepository
    reaction_repository: InMemoryReactionRepository
    transcript_store: LectureViewModelStore[TranscriptViewModel, GetTranscriptError]
    dialogue_store: LectureViewModelStore[DialogueViewModel, GetDialogueError]
    task_scheduler: ImmediateTaskScheduler
    amivoice_bridge: AmiVoiceStreamingBridge
    orchestrator: NoOpAiReactionOrchestrator
    start_lecture: BridgeAwareStartLectureController
    end_lecture: BridgeAwareEndLectureController
    record_utterance: RecordUtteranceController
    post_user_reaction: PostUserReactionController
    refresh_transcript: RefreshTranscriptController
    refresh_dialogue: RefreshDialogueController


def _resolve_amivoice_wiring(
    settings: Settings,
    *,
    session_factory: AmiVoiceWsSessionFactory | None,
    capture_source: AudioCaptureSource | None,
) -> tuple[AmiVoiceWsSessionFactory, AudioCaptureSource | None]:
    if session_factory is not None:
        return session_factory, capture_source
    if settings.amivoice_api_key:
        logger.debug(
            "AmiVoice wiring: Wrp live session (grammar=%s proxy=%s)",
            settings.amivoice_grammar_file_names,
            bool(settings.amivoice_proxy_server_name),
        )
        return (
            WrpAmiVoiceSessionFactory(
                ws_url=settings.amivoice_ws_url,
                proxy_server_name=settings.amivoice_proxy_server_name,
                grammar_file_names=settings.amivoice_grammar_file_names,
                receive_timeout_ms=settings.amivoice_receive_timeout_ms,
            ),
            capture_source
            or SoundDeviceAudioCaptureSource(device_name=settings.audio_capture_device),
        )
    logger.debug("AmiVoice wiring: Null session (AMIVOICE_API_KEY unset)")
    return NullAmiVoiceWsSessionFactory(), None


def build_deps(
    settings: Settings | None = None,
    *,
    orchestrator: NoOpAiReactionOrchestrator | None = None,
    session_factory: AmiVoiceWsSessionFactory | None = None,
    capture_source: AudioCaptureSource | None = None,
) -> AppDeps:
    settings = settings or load_settings()
    lecture_repository = InMemoryLectureRepository()
    reaction_repository = InMemoryReactionRepository()
    transcript_store: LectureViewModelStore[TranscriptViewModel, GetTranscriptError] = (
        LectureViewModelStore()
    )
    dialogue_store: LectureViewModelStore[DialogueViewModel, GetDialogueError] = (
        LectureViewModelStore()
    )
    task_scheduler = ImmediateTaskScheduler()

    start_lecture_uc = StartLectureUseCase(_lecture_repository=lecture_repository)
    end_lecture_uc = EndLectureUseCase(_lecture_repository=lecture_repository)
    record_utterance_uc = RecordUtteranceUseCase(_lecture_repository=lecture_repository)
    get_transcript_uc = GetTranscriptUseCase(_lecture_repository=lecture_repository)
    get_dialogue_uc = GetDialogueUseCase(
        _lecture_repository=lecture_repository,
        _reaction_repository=reaction_repository,
    )
    post_user_reaction_uc = PostUserReactionUseCase(
        _lecture_repository=lecture_repository,
        _reaction_repository=reaction_repository,
    )

    transcript_presenter = TranscriptPresenter(
        _mapper=TranscriptViewModelMapper(),
        _store=transcript_store,
    )
    dialogue_presenter = DialoguePresenter(
        _mapper=DialogueViewModelMapper(),
        _store=dialogue_store,
    )
    refresh_transcript = RefreshTranscriptController(
        _use_case=get_transcript_uc.execute,
        _presenter=transcript_presenter,
    )
    refresh_dialogue = RefreshDialogueController(
        _dialogue_use_case=get_dialogue_uc.execute,
        _transcript_use_case=get_transcript_uc.execute,
        _presenter=dialogue_presenter,
    )
    orchestrator = orchestrator or NoOpAiReactionOrchestrator()
    record_utterance = RecordUtteranceController(_use_case=record_utterance_uc.execute)
    ws_factory, audio_capture = _resolve_amivoice_wiring(
        settings,
        session_factory=session_factory,
        capture_source=capture_source,
    )
    amivoice_bridge = AmiVoiceStreamingBridge(
        _on_utterance=record_utterance.execute,
        _speaker_display_name=settings.amivoice_speaker_display_name,
        _session_factory=ws_factory,
        _api_key=settings.amivoice_api_key,
        _capture_source=audio_capture,
        _start_command=amivoice_start_command(settings.amivoice_grammar_file_names),
    )
    start_lecture_inner = StartLectureController(_use_case=start_lecture_uc.execute)
    end_lecture_inner = EndLectureController(_use_case=end_lecture_uc.execute)
    start_lecture = BridgeAwareStartLectureController(
        _inner=start_lecture_inner.execute,
        _on_started=amivoice_bridge.start_session,
    )
    end_lecture = BridgeAwareEndLectureController(
        _inner=end_lecture_inner.execute,
        _on_ended=lambda _lecture_id: amivoice_bridge.end_session(),
    )

    return AppDeps(
        settings=settings,
        lecture_repository=lecture_repository,
        reaction_repository=reaction_repository,
        transcript_store=transcript_store,
        dialogue_store=dialogue_store,
        task_scheduler=task_scheduler,
        amivoice_bridge=amivoice_bridge,
        orchestrator=orchestrator,
        start_lecture=start_lecture,
        end_lecture=end_lecture,
        record_utterance=record_utterance,
        post_user_reaction=PostUserReactionController(
            _use_case=post_user_reaction_uc.execute,
            _orchestrator=orchestrator,
        ),
        refresh_transcript=refresh_transcript,
        refresh_dialogue=refresh_dialogue,
    )


def create_app(deps: AppDeps | None = None, *, testing: bool = False) -> FastAPI:
    # testing=True のときも毎回新規 AppDeps（Phase0+ 統合テストの独立性）
    _ = testing
    deps = deps or build_deps()
    configure_logging(deps.settings)
    app = FastAPI(title="PairRadioListening")
    app.state.deps = deps

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_http_router(deps))
    return app


app = create_app()
