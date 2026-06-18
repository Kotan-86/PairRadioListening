# 仕様: docs/spec/framework.md#3.1, #5.3
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from framework.settings import load_settings
from interface_adapters.view_models.transcript_view_model import (
    TranscriptLineView,
    TranscriptViewModel,
)


@pytest.mark.phase0
def test_app_starts_and_returns_health_or_openapi(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "openapi" in openapi.json()


@pytest.mark.phase0
def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOST", "192.168.1.10")
    monkeypatch.setenv("PORT", "9001")
    settings = load_settings()
    assert settings.host == "192.168.1.10"
    assert settings.port == 9001


@pytest.mark.phase0
def test_view_model_store_present_and_read(client: TestClient, deps) -> None:
    view_model = TranscriptViewModel(
        lecture_id="lecture-store-1",
        lines=(
            TranscriptLineView(
                utterance_id="u-1",
                time_label="00:01",
                speaker_label="講師",
                body="こんにちは",
            ),
        ),
        error_message="",
    )
    deps.transcript_store.present(view_model)
    assert deps.transcript_store.get("lecture-store-1") is view_model

    start = client.post(
        "/api/lectures/start",
        json={
            "persona_profiles": [
                {
                    "id": "p1",
                    "display_name": "AI",
                    "persona_prompt": "prompt",
                },
            ],
        },
    )
    assert start.status_code == 201
    lecture_id = start.json()["lecture_id"]

    response = client.get(f"/api/lectures/{lecture_id}/transcript")
    assert response.status_code == 200
    body = response.json()
    assert body["lecture_id"] == lecture_id
    assert body["lines"] == []
    assert body["error_message"] == ""
    assert deps.transcript_store.get(lecture_id) is not None


@pytest.mark.phase0
def test_error_kind_maps_to_http_status(client: TestClient) -> None:
    response = client.post(
        "/api/lectures/start",
        json={
            "persona_profiles": [
                {
                    "id": "p1",
                    "display_name": "AI-1",
                    "persona_prompt": "prompt-1",
                },
                {
                    "id": "p2",
                    "display_name": "AI-2",
                    "persona_prompt": "prompt-2",
                },
            ],
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error_kind"] == "invalid_persona_profiles"

