# 仕様: docs/spec/framework_amivoice.md#4.5–4.7
from __future__ import annotations

from typing import Any

from framework.amivoice.payload_mapper import (
    extract_amivoice_body,
    is_successful_utterance_body,
)


def format_amivoice_connection_summary(
    *,
    ws_url: str,
    grammar_file_names: str,
    api_key_set: bool,
    proxy_configured: bool,
) -> str:
    """秘密情報を出さない接続設定の要約。"""
    return (
        f"ws_url={ws_url!r} grammar={grammar_file_names!r} "
        f"api_key_set={api_key_set} proxy_configured={proxy_configured}"
    )


def describe_amivoice_payload_skip(payload: dict[str, Any]) -> str:
    """map_amivoice_payload_to_event が None になる理由（デバッグ用）。"""
    body = extract_amivoice_body(payload)
    if body is None:
        return "no recognizable utterance body in payload"
    if not is_successful_utterance_body(body):
        return (
            f"not successful: code={body.get('code')!r} "
            f"message={body.get('message')!r} text_len={len(str(body.get('text', '')))}"
        )
    results = body.get("results")
    if not isinstance(results, list) or not results:
        return "results missing or empty"
    first = results[0]
    if not isinstance(first, dict):
        return "results[0] is not an object"
    start_ms = first.get("starttime")
    end_ms = first.get("endtime")
    utterance_id = body.get("utteranceid")
    if start_ms is None or end_ms is None or not str(utterance_id or "").strip():
        return (
            f"missing timing or utteranceid: start={start_ms!r} end={end_ms!r} "
            f"utteranceid={utterance_id!r}"
        )
    return "mappable (unexpected if caller got None)"
