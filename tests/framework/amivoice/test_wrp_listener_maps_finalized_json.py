# 仕様: docs/spec/framework_amivoice.md#4.5–4.7
from __future__ import annotations

import json

import pytest

from framework.amivoice.payload_mapper import map_amivoice_payload_to_event
from framework.amivoice.wrp_session import WrpBridgeListener
from tests.framework.helpers import amivoice_utterance_payload


@pytest.mark.phase1c
def test_wrp_listener_forwards_finalized_json_to_handler() -> None:
    payload = amivoice_utterance_payload(text="確定結果", utterance_id="wrp-1")
    received: list[str] = []
    listener = WrpBridgeListener(received.append)
    listener.resultFinalized(json.dumps(payload))
    assert len(received) == 1
    assert json.loads(received[0])["text"] == "確定結果"


@pytest.mark.phase1c
def test_wrp_listener_skips_r_prefixed_finalized() -> None:
    received: list[str] = []
    listener = WrpBridgeListener(received.append)
    listener.resultFinalized("\001\001\001\001\001" + '{"text":"skip"}')
    assert received == []


@pytest.mark.phase1c
def test_finalized_json_maps_to_utterance_event() -> None:
    payload = amivoice_utterance_payload(
        utterance_id="wrp-map-1",
        text="Wrp経路",
        start_ms=50,
        end_ms=900,
    )
    received: list[str] = []
    WrpBridgeListener(received.append).resultFinalized(json.dumps(payload))
    event = map_amivoice_payload_to_event(
        lecture_id="lec-wrp",
        speaker_display_name="講師",
        payload=json.loads(received[0]),
    )
    assert event is not None
    assert event.transcript == "Wrp経路"
    assert event.utterance_id == "wrp-map-1"
    assert event.start_ms == 50
    assert event.end_ms == 900
