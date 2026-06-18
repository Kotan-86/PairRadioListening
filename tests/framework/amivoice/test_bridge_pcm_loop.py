# 仕様: docs/spec/framework_amivoice.md#4.8
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from framework.amivoice.amivoice_streaming_bridge import AmiVoiceStreamingBridge
from framework.amivoice.audio_capture_source import FakeAudioCaptureSource
from framework.amivoice.null_ws_session import NullAmiVoiceWsSession, NullAmiVoiceWsSessionFactory
from framework.bootstrap import build_deps, create_app
from framework.settings import Settings
from tests.framework.amivoice.fake_utterance_ws_session import (
    UtteranceEmittingWsSession,
    UtteranceEmittingWsSessionFactory,
)
from tests.framework.helpers import amivoice_utterance_payload, start_lecture_body


@pytest.mark.phase1c
def test_bridge_starts_capture_on_start_session() -> None:
    pcm = b"\x00\x00" * 1600
    capture = FakeAudioCaptureSource(chunks=[pcm])
    bridge = AmiVoiceStreamingBridge(
        _on_utterance=lambda _e: None,
        _speaker_display_name="講師",
        _session_factory=NullAmiVoiceWsSessionFactory(),
        _api_key=None,
        _capture_source=capture,
    )
    bridge.start_session("lec-1")
    time.sleep(0.2)
    session = bridge.last_session
    assert isinstance(session, NullAmiVoiceWsSession)
    assert capture.started
    assert session.audio_chunks == [pcm]
    bridge.end_session()
    assert not capture.started


@pytest.mark.phase1c
def test_bridge_stops_capture_on_end_session() -> None:
    capture = FakeAudioCaptureSource(chunks=[b"\x00\x00" * 100, b"\x01\x00" * 100])
    bridge = AmiVoiceStreamingBridge(
        _on_utterance=lambda _e: None,
        _speaker_display_name="講師",
        _session_factory=NullAmiVoiceWsSessionFactory(),
        _api_key=None,
        _capture_source=capture,
    )
    bridge.start_session("lec-2")
    time.sleep(0.15)
    bridge.end_session()
    session = bridge.last_session
    assert isinstance(session, NullAmiVoiceWsSession)
    assert session.commands[-1] == "e"
    assert not capture.started


@pytest.mark.phase1c
def test_amivoice_result_updates_transcript(client: TestClient) -> None:
    utterance = amivoice_utterance_payload(
        utterance_id="bridge-e2e-1",
        text="PCM経路の文字起こし",
    )
    settings = Settings(
        host="127.0.0.1",
        port=8000,
        amivoice_api_key="integration-test-key",
        amivoice_ws_url="wss://acp-api.amivoice.com/v1/",
        amivoice_proxy_server_name=None,
        amivoice_grammar_file_names="-a2-ja-general",
        amivoice_receive_timeout_ms=0,
        audio_capture_device=None,
        amivoice_speaker_display_name="講師",
        gemini_api_key=None,
        llm_api_key=None,
        llm_model="gemini-3.1-flash-lite",
        llm_rpm_limit=15,
        llm_rpd_limit=500,
        log_level="INFO",
        amivoice_debug=False,
    )
    pcm = b"\x00\x00" * 3200
    capture = FakeAudioCaptureSource(chunks=[pcm])
    factory = UtteranceEmittingWsSessionFactory(utterance_payload=utterance)
    deps = build_deps(settings, session_factory=factory, capture_source=capture)
    app = create_app(deps, testing=True)
    with TestClient(app) as local_client:
        start = local_client.post("/api/lectures/start", json=start_lecture_body())
        lecture_id = start.json()["lecture_id"]
        time.sleep(0.5)
        local_client.post(f"/api/lectures/{lecture_id}/end")
        time.sleep(0.3)

        transcript = local_client.get(f"/api/lectures/{lecture_id}/transcript")
        body = transcript.json()
        assert len(body["lines"]) >= 1
        assert any("PCM経路" in line["body"] for line in body["lines"])
    assert isinstance(deps.amivoice_bridge.last_session, UtteranceEmittingWsSession)
