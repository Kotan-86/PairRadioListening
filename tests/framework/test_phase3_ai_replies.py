# 仕様: docs/spec/framework_llm.md#8.1, docs/spec/framework_llm.md#8.2
from __future__ import annotations

import time
import pytest
from dataclasses import dataclass
from fastapi.testclient import TestClient

from framework.bootstrap import build_deps, create_app
from framework.llm.fake_llm_analyzer import FakeLlmAnalyzer
from framework.llm.fake_reaction_text_generator import FakeReactionTextGenerator
from framework.schedulers.immediate_task_scheduler import ImmediateTaskScheduler
from framework.schedulers.thread_pool_task_scheduler import ThreadPoolTaskScheduler
from framework.settings import Settings
from tests.framework.helpers import reaction_body, start_lecture_body, utterance_body


def _phase3_client(
    *,
    scheduler: ImmediateTaskScheduler | ThreadPoolTaskScheduler | None = None,
    fake_analyzer: FakeLlmAnalyzer | None = None,
    fake_text_generator: FakeReactionTextGenerator | None = None,
) -> tuple[TestClient, object]:
    settings = Settings(
        host="127.0.0.1",
        port=8000,
        amivoice_api_key=None,
        amivoice_ws_url="wss://example.test/",
        amivoice_proxy_server_name=None,
        amivoice_grammar_file_names="-a2-ja-general",
        amivoice_receive_timeout_ms=0,
        audio_capture_device=None,
        amivoice_speaker_display_name="講師",
        gemini_api_key=None,
        llm_api_key="fake",
        llm_model="gemini-test",
        llm_rpm_limit=15,
        llm_rpd_limit=500,
        log_level="WARNING",
        amivoice_debug=False,
    )
    deps = build_deps(
        settings=settings,
        task_scheduler=scheduler or ImmediateTaskScheduler(),
        fake_analyzer=fake_analyzer,
        fake_text_generator=fake_text_generator,
    )
    return TestClient(create_app(deps, testing=True)), deps


def _bootstrap_lecture_with_utterance(client: TestClient) -> str:
    start = client.post("/api/lectures/start", json=start_lecture_body())
    lecture_id = start.json()["lecture_id"]
    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(lecture_id, end_ms=1200, speech_text="講義の要点"),
    )
    return lecture_id


@pytest.mark.phase3
def test_post_reaction_triggers_ai_line_in_dialogue():
    client, _deps = _phase3_client()

    lecture_id = _bootstrap_lecture_with_utterance(client)
    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(
            reaction_text="ここが気になります",
            lecture_time_anchor=1200,
            speaker_display_name="ユーザー",
        ),
    )
    assert post.status_code == 200

    dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
    assert dialogue.status_code == 200
    lines = dialogue.json()["lines"]
    assert len(lines) == 2
    assert lines[0]["speaker_label"] == "ユーザー"
    assert lines[0]["body"] == "ここが気になります"
    assert lines[1]["speaker_label"] == "AI"
    assert "Fake AI" in lines[1]["body"]


@pytest.mark.phase3
def test_ai_line_has_reference_quote_label():
    client, _deps = _phase3_client()

    lecture_id = _bootstrap_lecture_with_utterance(client)
    client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(
            reaction_text="もう少し詳しく",
            lecture_time_anchor=1200,
            speaker_display_name="ユーザー",
        ),
    )

    dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
    ai_line = dialogue.json()["lines"][1]
    assert ai_line["reference_quote_label"]
    assert "ユーザー" in ai_line["reference_quote_label"]
    assert "もう少し詳しく" in ai_line["reference_quote_label"]


@pytest.mark.phase3
def test_record_utterance_does_not_add_ai_line():
    client, deps = _phase3_client()

    lecture_id = _bootstrap_lecture_with_utterance(client)
    assert isinstance(deps.orchestrator, object)

    client.post(
        "/internal/amivoice/utterances",
        json=utterance_body(
            lecture_id,
            utterance_id="utt-2",
            start_ms=1300,
            end_ms=2500,
            speech_text="続きの講義",
        ),
    )

    dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
    assert dialogue.json()["lines"] == []


@pytest.mark.phase3
def test_orchestrator_does_not_block_post_response():
    fake_analyzer = FakeLlmAnalyzer(policy_delay_s=0.2)
    fake_text_generator = FakeReactionTextGenerator(text_delay_s=0.2)
    client, _deps = _phase3_client(
        scheduler=ThreadPoolTaskScheduler(),
        fake_analyzer=fake_analyzer,
        fake_text_generator=fake_text_generator,
    )

    lecture_id = _bootstrap_lecture_with_utterance(client)
    started = time.perf_counter()
    post = client.post(
        f"/api/lectures/{lecture_id}/reactions",
        json=reaction_body(
            reaction_text="非同期テスト",
            lecture_time_anchor=1200,
        ),
    )
    elapsed = time.perf_counter() - started

    assert post.status_code == 200
    assert elapsed < 0.15

    deadline = time.time() + 2.0
    while time.time() < deadline:
        dialogue = client.get(f"/api/lectures/{lecture_id}/dialogue")
        if len(dialogue.json()["lines"]) == 2:
            break
        time.sleep(0.05)
    else:
        pytest.fail("AI line did not appear within timeout")
