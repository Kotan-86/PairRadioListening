# 仕様: docs/spec/framework.md#2.3
from __future__ import annotations

from typing import Any


def persona_profile_body(
    *,
    profile_id: str = "persona-1",
    display_name: str = "AI",
    persona_prompt: str = "prompt",
) -> dict[str, str]:
    return {
        "id": profile_id,
        "display_name": display_name,
        "persona_prompt": persona_prompt,
    }


def start_lecture_body(**kwargs: Any) -> dict[str, Any]:
    persona = kwargs.pop("persona", None) or persona_profile_body()
    title = kwargs.pop("title", "")
    return {
        "persona_profiles": [persona],
        "title": title,
    }


def utterance_body(
    lecture_id: str,
    *,
    utterance_id: str = "utt-1",
    speech_text: str = "こんにちは",
    speaker_display_name: str = "講師",
    start_ms: int = 0,
    end_ms: int = 1200,
) -> dict[str, Any]:
    return {
        "lecture_id": lecture_id,
        "utterance_id": utterance_id,
        "speech_text": speech_text,
        "speaker_display_name": speaker_display_name,
        "start_ms": start_ms,
        "end_ms": end_ms,
    }


def reaction_body(
    *,
    reaction_text: str = "いい話ですね",
    lecture_time_anchor: int = 1200,
    speaker_display_name: str = "ユーザー",
    reply_target: dict[str, str] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "reaction_text": reaction_text,
        "lecture_time_anchor": lecture_time_anchor,
        "speaker_display_name": speaker_display_name,
    }
    if reply_target is not None:
        body["reply_target"] = reply_target
    return body


def amivoice_utterance_payload(
    *,
    utterance_id: str = "amivoice-utt-1",
    text: str = "書き起こし結果",
    start_ms: int = 0,
    end_ms: int = 1200,
) -> dict[str, Any]:
    return {
        "results": [
            {
                "starttime": start_ms,
                "endtime": end_ms,
                "tokens": [],
                "confidence": 0.95,
                "tags": [],
                "rulename": "",
                "text": text,
            },
        ],
        "text": text,
        "code": "",
        "message": "",
        "utteranceid": utterance_id,
    }
