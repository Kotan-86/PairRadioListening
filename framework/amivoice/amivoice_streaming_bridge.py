# 仕様: docs/spec/framework_amivoice.md#4
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from framework.amivoice.audio_capture_source import AudioCaptureSource
from framework.amivoice.diagnostics import describe_amivoice_payload_skip
from framework.amivoice.payload_mapper import map_amivoice_payload_to_event
from framework.amivoice.session_commands import (
    DEFAULT_GRAMMAR_FILE_NAMES,
    amivoice_start_command,
)
from framework.amivoice.ws_session import AmiVoiceWsSession, AmiVoiceWsSessionFactory
from interface_adapters.events.speech_recognition_utterance_event import (
    SpeechRecognitionUtteranceEvent,
)
from interface_adapters.outcomes.record_utterance_outcome import RecordUtteranceOutcome

_END_COMMAND = "e"

logger = logging.getLogger(__name__)


@dataclass
class AmiVoiceStreamingBridge:
    """AmiVoice WebSocket セッションと transcription_port（record_utterance）を接続する。"""

    _on_utterance: Callable[[SpeechRecognitionUtteranceEvent], RecordUtteranceOutcome]
    _speaker_display_name: str
    _session_factory: AmiVoiceWsSessionFactory
    _api_key: str | None
    _capture_source: AudioCaptureSource | None = None
    _start_command: str = field(
        default_factory=lambda: amivoice_start_command(DEFAULT_GRAMMAR_FILE_NAMES)
    )
    _lecture_id: str | None = field(default=None, init=False)
    _session: AmiVoiceWsSession | None = field(default=None, init=False)
    last_session: AmiVoiceWsSession | None = field(default=None, init=False)

    def start_session(self, lecture_id: str) -> None:
        logger.debug(
            "Bridge start_session lecture_id=%s start_command=%r capture=%s",
            lecture_id,
            self._start_command,
            self._capture_source is not None,
        )
        if self._session is not None:
            logger.debug("Bridge ending previous session before start")
            self.end_session()
        self._lecture_id = lecture_id
        self._session = self._session_factory.create(
            api_key=self._api_key or "",
            lecture_id=lecture_id,
        )
        self.last_session = self._session
        self._session.set_message_handler(self._on_ws_message)
        self._session.send_start_command(self._start_command)
        if self._capture_source is not None:
            self._capture_source.start(self._forward_pcm)
            logger.debug("Bridge audio capture started lecture_id=%s", lecture_id)

    def end_session(self) -> None:
        logger.debug("Bridge end_session lecture_id=%s", self._lecture_id)
        if self._capture_source is not None:
            self._capture_source.stop()
            logger.debug("Bridge audio capture stopped")
        if self._session is not None:
            self._session.send_end_command(_END_COMMAND)
            self._session.close()
        self._session = None
        self._lecture_id = None

    def _forward_pcm(self, pcm_bytes: bytes) -> None:
        session = self._session
        if session is not None:
            session.send_audio(pcm_bytes)

    def handle_payload(self, payload: dict[str, Any]) -> RecordUtteranceOutcome | None:
        """WebSocket 以外（単体テスト）から AmiVoice JSON を注入する。"""
        if self._lecture_id is None:
            return None
        event = map_amivoice_payload_to_event(
            lecture_id=self._lecture_id,
            speaker_display_name=self._speaker_display_name,
            payload=payload,
        )
        if event is None:
            logger.debug(
                "Bridge handle_payload skipped: %s",
                describe_amivoice_payload_skip(payload),
            )
            return None
        logger.debug(
            "Bridge record_utterance lecture_id=%s utterance_id=%s transcript_len=%d",
            event.lecture_id,
            event.utterance_id,
            len(event.transcript),
        )
        outcome = self._on_utterance(event)
        logger.debug("Bridge record_utterance outcome success=%s", outcome.success)
        return outcome

    def _on_ws_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Bridge JSON decode failed len=%d", len(raw))
            return
        if not isinstance(payload, dict):
            logger.debug("Bridge ignored non-object payload type=%s", type(payload).__name__)
            return
        self.handle_payload(payload)
