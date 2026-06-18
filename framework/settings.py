# 仕様: docs/spec/framework.md#1.4
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from framework.amivoice.session_commands import DEFAULT_GRAMMAR_FILE_NAMES


def _optional_str(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw.strip())


def _truthy_env(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    """Composition root 起動時に読み込む環境変数（Domain / Application / Interface からは参照しない）。"""

    host: str
    port: int
    amivoice_api_key: str | None
    amivoice_ws_url: str
    amivoice_proxy_server_name: str | None
    amivoice_grammar_file_names: str
    amivoice_receive_timeout_ms: int
    audio_capture_device: str | None
    amivoice_speaker_display_name: str
    gemini_api_key: str | None
    llm_api_key: str | None
    llm_model: str
    llm_rpm_limit: int
    llm_rpd_limit: int
    log_level: str
    amivoice_debug: bool

    @property
    def effective_llm_api_key(self) -> str | None:
        return self.gemini_api_key or self.llm_api_key


def load_settings(*, env_file: str | None = None) -> Settings:
    load_dotenv(env_file)
    return Settings(
        host=os.getenv("HOST", "127.0.0.1").strip(),
        port=_int_env("PORT", 8000),
        amivoice_api_key=_optional_str("AMIVOICE_API_KEY"),
        amivoice_ws_url=os.getenv(
            "AMIVOICE_WS_URL", "wss://acp-api.amivoice.com/v1/"
        ).strip(),
        amivoice_proxy_server_name=_optional_str("AMIVOICE_PROXY_SERVER_NAME"),
        amivoice_grammar_file_names=os.getenv(
            "AMIVOICE_GRAMMAR_FILE_NAMES", DEFAULT_GRAMMAR_FILE_NAMES
        ).strip(),
        amivoice_receive_timeout_ms=_int_env("AMIVOICE_RECEIVE_TIMEOUT_MS", 0),
        audio_capture_device=_optional_str("AUDIO_CAPTURE_DEVICE"),
        amivoice_speaker_display_name=os.getenv(
            "AMIVOICE_SPEAKER_DISPLAY_NAME", "講師"
        ).strip(),
        gemini_api_key=_optional_str("GEMINI_API_KEY"),
        llm_api_key=_optional_str("LLM_API_KEY"),
        llm_model=os.getenv("LLM_MODEL", "gemini-3.1-flash-lite").strip(),
        llm_rpm_limit=_int_env("LLM_RPM_LIMIT", 15),
        llm_rpd_limit=_int_env("LLM_RPD_LIMIT", 500),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
        amivoice_debug=_truthy_env("AMIVOICE_DEBUG"),
    )
