# 仕様: docs/spec/framework.md#4.1–4.3, #4.5
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.framework.helpers import start_lecture_body, utterance_body


@pytest.mark.phase1
def test_start_lecture_returns_lecture_id(client: TestClient) -> None:
    response = client.post("/api/lectures/start", json=start_lecture_body())
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["lecture_id"]
    assert body["lecture_id"] not in ("None", "")


@pytest.mark.phase1
def test_end_lecture_closes_session(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    end = client.post(f"/api/lectures/{lecture_id}/end")
    assert end.status_code == 200
    body = end.json()
    assert body["success"] is True
    assert body["lecture_id"] == lecture_id


@pytest.mark.phase1
def test_inject_utterance_then_transcript_has_lines(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    first = client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(
            lecture_id,
            utterance_id="utt-1",
            speech_text="最初の発話",
            start_ms=0,
            end_ms=1200,
        ),
    )
    second = client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(
            lecture_id,
            utterance_id="utt-2",
            speech_text="二番目の発話",
            start_ms=1300,
            end_ms=2500,
        ),
    )
    assert first.status_code == 200
    assert second.status_code == 200

    transcript = client.get(f"/api/lectures/{lecture_id}/transcript")
    assert transcript.status_code == 200
    body = transcript.json()
    assert body["lecture_id"] == lecture_id
    assert len(body["lines"]) == 2
    for line in body["lines"]:
        assert line["time_label"]
        assert line["body"]


@pytest.mark.phase1
def test_transcript_error_state(client: TestClient) -> None:
    response = client.get("/api/lectures/missing-lecture/transcript")
    assert response.status_code == 200
    body = response.json()
    assert body["lines"] == []
    assert body["error_message"]


@pytest.mark.phase1
def test_record_utterance_does_not_trigger_llm(client: TestClient, deps) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    response = client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(lecture_id),
    )
    assert response.status_code == 200
    assert deps.orchestrator.call_count == 0
