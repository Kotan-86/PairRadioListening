# 仕様: docs/spec/framework.md#4.4–4.6, docs/spec/application.md#post_user_reaction
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.framework.helpers import reaction_body, start_lecture_body, utterance_body


@pytest.mark.phase2
def test_transcript_exposes_latest_anchor_ms(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(
            lecture_id,
            utterance_id="utt-1",
            start_ms=0,
            end_ms=1200,
        ),
    )
    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(
            lecture_id,
            utterance_id="utt-2",
            start_ms=1300,
            end_ms=2500,
        ),
    )

    transcript = client.get(f"/api/lectures/{lecture_id}/transcript")
    assert transcript.status_code == 200
    body = transcript.json()
    assert body["latest_anchor_ms"] == 2500


@pytest.mark.phase2
def test_post_reaction_appears_in_dialogue(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(lecture_id, end_ms=1200),
    )

    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(
            reaction_text="とても参考になりました",
            lecture_time_anchor=1200,
            speaker_display_name="ユーザー",
        ),
    )
    assert post.status_code == 200
    assert post.json()["success"] is True

    dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
    assert dialogue.status_code == 200
    lines = dialogue.json()["lines"]
    assert len(lines) == 1
    user_line = lines[0]
    assert user_line["speaker_label"] == "ユーザー"
    assert user_line["body"] == "とても参考になりました"
    assert user_line["reference_time_label"]


@pytest.mark.phase2
def test_post_reaction_fails_without_utterance(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(lecture_time_anchor=0),
    )
    assert post.status_code == 409
    body = post.json()
    assert body["success"] is False
    assert body["error_kind"] == "timeline_not_established"


@pytest.mark.phase2
def test_post_reaction_after_end_fails(client: TestClient) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(lecture_id, end_ms=1200),
    )
    client.post(f"/api/lectures/{lecture_id}/end")

    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(lecture_time_anchor=1200),
    )
    assert post.status_code == 409
    body = post.json()
    assert body["success"] is False
    assert body["error_kind"] == "lecture_closed"


@pytest.mark.phase2
def test_post_does_not_add_ai_line(client: TestClient, deps) -> None:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]

    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(lecture_id, end_ms=1200),
    )

    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(
            reaction_text="質問です",
            lecture_time_anchor=1200,
            speaker_display_name="ユーザー",
        ),
    )
    assert post.status_code == 200

    dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
    lines = dialogue.json()["lines"]
    assert len(lines) == 1
    assert lines[0]["speaker_label"] == "ユーザー"
    assert deps.orchestrator.call_count == 1
