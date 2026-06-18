# 仕様: docs/spec/framework_amivoice.md#4.5–4.7
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from interface_adapters.events.speech_recognition_utterance_event import (
    SpeechRecognitionUtteranceEvent,
)


def extract_amivoice_body(payload: dict[str, Any]) -> dict[str, Any] | None:
    nested = payload.get("body")
    if isinstance(nested, dict):
        return nested
    if any(key in payload for key in ("code", "message", "text", "results", "utteranceid")):
        return payload
    return None


def is_successful_utterance_body(body: dict[str, Any]) -> bool:
    code = str(body.get("code", ""))
    message = str(body.get("message", ""))
    text = str(body.get("text", ""))
    return code == "" and message == "" and text != ""


def map_amivoice_payload_to_event(
    *,
    lecture_id: str,
    speaker_display_name: str,
    payload: dict[str, Any],
) -> SpeechRecognitionUtteranceEvent | None:
    body = extract_amivoice_body(payload)
    if body is None:
        logger.debug("AmiVoice payload skipped: no body")
        return None
    if not is_successful_utterance_body(body):
        logger.debug(
            "AmiVoice payload skipped: code=%r message=%r text_empty=%s",
            body.get("code"),
            body.get("message"),
            not str(body.get("text", "")).strip(),
        )
        return None

    results = body.get("results")
    if not isinstance(results, list) or not results:
        logger.debug("AmiVoice payload skipped: results empty")
        return None
    first = results[0]
    if not isinstance(first, dict):
        logger.debug("AmiVoice payload skipped: results[0] not dict")
        return None

    start_ms = first.get("starttime")
    end_ms = first.get("endtime")
    utterance_id = body.get("utteranceid")
    if start_ms is None or end_ms is None or not str(utterance_id or "").strip():
        logger.debug(
            "AmiVoice payload skipped: start=%r end=%r utteranceid=%r",
            start_ms,
            end_ms,
            utterance_id,
        )
        return None

    logger.debug(
        "AmiVoice payload mapped: utterance_id=%s transcript_len=%d",
        utterance_id,
        len(str(body["text"])),
    )
    return SpeechRecognitionUtteranceEvent(
        lecture_id=lecture_id,
        utterance_id=str(utterance_id),
        start_ms=int(start_ms),
        end_ms=int(end_ms),
        transcript=str(body["text"]),
        speaker_display_name=speaker_display_name,
    )
