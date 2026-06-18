# 仕様: docs/spec/framework_amivoice.md#4.7
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from framework.amivoice.null_ws_session import NullAmiVoiceWsSession
from framework.amivoice.payload_mapper import map_amivoice_payload_to_event
from tests.framework.helpers import amivoice_utterance_payload, start_lecture_body


@pytest.mark.phase1
def test_amivoice_payload_maps_to_utterance_event() -> None:
    payload = amivoice_utterance_payload(
        utterance_id="amivoice-123",
        text="書き起こし結果",
        start_ms=100,
        end_ms=2200,
    )
    event = map_amivoice_payload_to_event(
        lecture_id="lecture-1",
        speaker_display_name="講師A",
        payload=payload,
    )
    assert event is not None
    assert event.lecture_id == "lecture-1"
    assert event.utterance_id == "amivoice-123"
    assert event.start_ms == 100
    assert event.end_ms == 2200
    assert event.transcript == "書き起こし結果"
    assert event.speaker_display_name == "講師A"


@pytest.mark.phase1
def test_start_lecture_starts_bridge_session(client: TestClient, deps) -> None:
    response = client.post("/api/lectures/start", json=start_lecture_body())
    assert response.status_code == 201
    lecture_id = response.json()["lecture_id"]

    session = deps.amivoice_bridge.last_session
    assert isinstance(session, NullAmiVoiceWsSession)
    assert session.lecture_id == lecture_id
    assert session.commands == ["s LSB16K -a2-ja-general"]
