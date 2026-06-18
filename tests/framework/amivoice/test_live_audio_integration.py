# 仕様: docs/spec/framework_amivoice.md#5.2
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from framework.amivoice.audio_capture_source import (
    SoundDeviceAudioCaptureSource,
    resolve_input_device_index,
)
from framework.amivoice.session_commands import amivoice_start_command
from framework.amivoice.wrp_session import WrpAmiVoiceSession
from framework.bootstrap import build_deps, create_app
from framework.settings import load_settings
from tests.framework.helpers import start_lecture_body


def _integration_settings():
    """integration テストでも .env を読み込む（pytest は load_dotenv しないため）。"""
    return load_settings()


def _api_key_configured() -> bool:
    return bool(_integration_settings().amivoice_api_key)


def _vb_cable_available() -> bool:
    settings = _integration_settings()
    return (
        resolve_input_device_index(settings.audio_capture_device) is not None
    )


@pytest.mark.integration
@pytest.mark.phase1c
def test_live_amivoice_wrp_with_real_key() -> None:
    """実 AmiVoice へ接続。社内プロキシ必須時は .env に AMIVOICE_PROXY_SERVER_NAME を設定。"""
    if not _api_key_configured():
        pytest.skip("AMIVOICE_API_KEY is not set")
    settings = _integration_settings()
    api_key = settings.amivoice_api_key or ""
    ws_url = settings.amivoice_ws_url
    proxy = settings.amivoice_proxy_server_name
    session = WrpAmiVoiceSession(
        lecture_id="integration-live",
        api_key=api_key,
        ws_url=ws_url,
        proxy_server_name=proxy,
        grammar_file_names=settings.amivoice_grammar_file_names,
    )
    try:
        session.send_start_command(
            amivoice_start_command(settings.amivoice_grammar_file_names)
        )
        silence = b"\x00\x00" * 16_000
        for _ in range(5):
            session.send_audio(silence)
            time.sleep(0.1)
        session.send_end_command("e")
        time.sleep(1.0)
    finally:
        session.close()


@pytest.mark.integration
@pytest.mark.phase1c
def test_vb_cable_capture_five_seconds() -> None:
    if not _vb_cable_available():
        pytest.skip("VB-Cable capture device not found")
    capture = SoundDeviceAudioCaptureSource(
        device_name=_integration_settings().audio_capture_device,
    )
    chunks: list[bytes] = []

    capture.start(chunks.append)
    time.sleep(5.0)
    capture.stop()
    assert any(len(chunk) > 0 for chunk in chunks)


@pytest.mark.integration
@pytest.mark.phase1c
def test_live_lecture_transcript_with_real_services() -> None:
    if not _api_key_configured():
        pytest.skip("AMIVOICE_API_KEY is not set")
    if not _vb_cable_available():
        pytest.skip("VB-Cable capture device not found")

    settings = _integration_settings()
    deps = build_deps(settings)
    app = create_app(deps, testing=True)
    with TestClient(app) as client:
        start = client.post("/api/lectures/start", json=start_lecture_body())
        assert start.status_code == 201
        lecture_id = start.json()["lecture_id"]
        time.sleep(5.0)
        client.post(f"/api/lectures/{lecture_id}/end")
        time.sleep(2.0)
        transcript = client.get(f"/api/lectures/{lecture_id}/transcript")
        body = transcript.json()
        if len(body.get("lines", [])) < 1:
            pytest.skip(
                "No transcript lines (play audio to VB-Cable Input during the test)"
            )
