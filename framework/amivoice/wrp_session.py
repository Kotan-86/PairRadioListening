# 仕様: docs/spec/framework_amivoice.md#4.2
from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
import numpy as np

from framework.amivoice.session_commands import (
    DEFAULT_CODEC,
    DEFAULT_GRAMMAR_FILE_NAMES,
    amivoice_start_command,
)
from framework.amivoice.diagnostics import format_amivoice_connection_summary
from framework.amivoice.wrp_import import Wrp, WrpListener

logger = logging.getLogger(__name__)

DEFAULT_WS_URL = "wss://acp-api.amivoice.com/v1/"
_CONNECT_TIMEOUT_MS = 30_000
_RECEIVE_TIMEOUT_MS = 0
_BACKPRESSURE_SLEEP_MS = 50
_R_RESULT_PREFIX = "\001\001\001\001\001"
_RESULT_LOG_PREVIEW_CHARS = 300


def _pcm_rms_int16(pcm_bytes: bytes) -> int:
    if not pcm_bytes:
        return 0
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    if samples.size == 0:
        return 0
    # int16 の二乗でオーバーフローしないよう float64 へ上げる
    return int(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


class WrpBridgeListener(WrpListener):
    """Wrp スレッドから確定 JSON のみキューへ渡す（UC は別ワーカー）。"""

    def __init__(self, on_finalized: Callable[[str], None]) -> None:
        self._on_finalized = on_finalized

    def resultFinalized(self, result: str) -> None:  # noqa: N802
        if not result or result.startswith(_R_RESULT_PREFIX):
            logger.debug("resultFinalized ignored (empty or R-prefix aggregate)")
            return
        preview = result[:200] + ("..." if len(result) > 200 else "")
        logger.debug(
            "resultFinalized enqueued len=%d preview=%r",
            len(result),
            preview,
        )
        self._on_finalized(result)

    def utteranceStarted(self, start_time: int) -> None:  # noqa: N802, ARG002
        logger.debug("AmiVoice utteranceStarted: %s", start_time)

    def utteranceEnded(self, end_time: int) -> None:  # noqa: N802, ARG002
        logger.debug("AmiVoice utteranceEnded: %s", end_time)

    def resultCreated(self) -> None:  # noqa: N802
        pass

    def resultUpdated(self, result: str) -> None:  # noqa: N802
        preview = result[:_RESULT_LOG_PREVIEW_CHARS]
        if len(result) > _RESULT_LOG_PREVIEW_CHARS:
            preview += "..."
        logger.debug("resultUpdated len=%d preview=%r", len(result), preview)

    def eventNotified(self, event_id: str, event_message: str) -> None:  # noqa: N802
        logger.debug("AmiVoice event %s: %s", event_id, event_message)

    def TRACE(self, message: str) -> None:  # noqa: N802
        if message.startswith("ERROR:"):
            logger.error("%s", message)
        elif message.startswith("WARNING:"):
            logger.warning("%s", message)
        else:
            logger.debug("%s", message)


@dataclass
class WrpAmiVoiceSession:
    """公式 Wrp クライアントによる AmiVoiceWsSession 実装。"""

    lecture_id: str
    api_key: str
    ws_url: str = DEFAULT_WS_URL
    proxy_server_name: str | None = None
    grammar_file_names: str = DEFAULT_GRAMMAR_FILE_NAMES
    connect_timeout_ms: int = _CONNECT_TIMEOUT_MS
    receive_timeout_ms: int = _RECEIVE_TIMEOUT_MS
    _start_command: str = field(init=False)
    _handler: Callable[[str], None] | None = field(default=None, init=False)
    _message_queue: queue.Queue[str | None] = field(default_factory=queue.Queue, init=False)
    _worker: threading.Thread | None = field(default=None, init=False)
    _wrp: Wrp = field(init=False)
    _feeding: bool = field(default=False, init=False)
    audio_chunks_sent: list[bytes] = field(default_factory=list, init=False)
    _feed_fail_count: int = field(default=0, init=False)
    _rms_log_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._start_command = amivoice_start_command(self.grammar_file_names)
        wrp = Wrp.construct()
        wrp.setListener(WrpBridgeListener(self._enqueue_finalized))
        wrp.setServerURL(self.ws_url)
        wrp.setCodec(DEFAULT_CODEC)
        wrp.setGrammarFileNames(self.grammar_file_names)
        if self.api_key:
            wrp.setAuthorization(self.api_key)
        if self.proxy_server_name:
            wrp.setProxyServerName(self.proxy_server_name)
        wrp.setConnectTimeout(self.connect_timeout_ms)
        wrp.setReceiveTimeout(self.receive_timeout_ms)
        self._wrp = wrp
        logger.debug(
            "Wrp session configured lecture_id=%s %s",
            self.lecture_id,
            format_amivoice_connection_summary(
                ws_url=self.ws_url,
                grammar_file_names=self.grammar_file_names,
                api_key_set=bool(self.api_key),
                proxy_configured=bool(self.proxy_server_name),
            ),
        )

    def _wrp_debug_status(self) -> str:
        state = getattr(self._wrp, "state_", "?")
        return (
            f"connected={self._wrp.isConnected()} state={state} "
            f"waiting_results={self._wrp.getWaitingResults()} "
            f"feeding_flag={self._feeding} pcm_chunks={len(self.audio_chunks_sent)} "
            f"feed_failures={self._feed_fail_count} last_message={self._wrp.getLastMessage()!r}"
        )

    def set_message_handler(self, handler: Callable[[str], None]) -> None:
        self._handler = handler
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(
                target=self._run_message_worker,
                name=f"wrp-msg-{self.lecture_id}",
                daemon=True,
            )
            self._worker.start()

    def send_start_command(self, command: str) -> None:
        if command != self._start_command:
            raise ValueError(f"Unsupported AmiVoice start command: {command!r}")
        logger.debug(
            "Wrp connect starting lecture_id=%s command=%r",
            self.lecture_id,
            command,
        )
        if not self._wrp.connect():
            logger.debug("Wrp connect failed: %s", self._wrp_debug_status())
            raise ConnectionError(self._wrp.getLastMessage())
        logger.debug("Wrp connect ok: %s", self._wrp_debug_status())
        if not self._wrp.feedDataResume():
            message = self._wrp.getLastMessage()
            logger.debug("Wrp feedDataResume failed: %s", self._wrp_debug_status())
            self._wrp.disconnect()
            raise ConnectionError(message)
        self._feeding = True
        self._feed_fail_count = 0
        logger.info(
            "AmiVoice Wrp session started lecture_id=%s url=%s grammar=%s",
            self.lecture_id,
            self.ws_url,
            self.grammar_file_names,
        )
        logger.debug("Wrp feedDataResume ok: %s", self._wrp_debug_status())

    def send_audio(self, pcm_bytes: bytes) -> None:
        if not pcm_bytes:
            return
        if not self._feeding:
            logger.debug(
                "send_audio skipped (_feeding=False) bytes=%d %s",
                len(pcm_bytes),
                self._wrp_debug_status(),
            )
            return
        while self._wrp.getWaitingResults() > 1:
            self._wrp.sleep(_BACKPRESSURE_SLEEP_MS)
        length = len(pcm_bytes)
        pcm_rms = _pcm_rms_int16(pcm_bytes)
        self._rms_log_count += 1
        if self._rms_log_count <= 3 or self._rms_log_count % 50 == 0:
            logger.debug(
                "PCM level sample #%d bytes=%d rms=%d waiting_results=%d",
                self._rms_log_count,
                length,
                pcm_rms,
                self._wrp.getWaitingResults(),
            )
        if not self._wrp.feedData(pcm_bytes, 0, length):
            self._feed_fail_count += 1
            last_message = self._wrp.getLastMessage()
            logger.debug(
                "feedData failed (#%d, %d bytes): %s",
                self._feed_fail_count,
                length,
                self._wrp_debug_status(),
            )
            if self._feed_fail_count <= 3 or self._feed_fail_count % 50 == 0:
                logger.warning(
                    "AmiVoice feedData failed (#%d): %s",
                    self._feed_fail_count,
                    last_message,
                )
            state = getattr(self._wrp, "state_", None)
            if state == 5 or "timed out" in str(last_message).lower():
                logger.error(
                    "AmiVoice session moved to error state; stop PCM send: %s",
                    self._wrp_debug_status(),
                )
                self._feeding = False
            return
        self.audio_chunks_sent.append(pcm_bytes)
        chunk_count = len(self.audio_chunks_sent)
        if chunk_count == 1 or chunk_count % 50 == 0:
            total_bytes = sum(len(c) for c in self.audio_chunks_sent)
            logger.debug(
                "feedData ok: chunks=%d total_pcm_bytes=%d %s",
                chunk_count,
                total_bytes,
                self._wrp_debug_status(),
            )

    def send_end_command(self, command: str) -> None:
        _ = command
        if not self._feeding:
            logger.debug("send_end_command skipped (_feeding=False)")
            return
        logger.debug("Wrp feedDataPause starting: %s", self._wrp_debug_status())
        if not self._wrp.feedDataPause():
            logger.warning(
                "AmiVoice feedDataPause failed: %s", self._wrp.getLastMessage()
            )
        else:
            logger.debug("Wrp feedDataPause ok: %s", self._wrp_debug_status())
        self._feeding = False

    def close(self) -> None:
        logger.debug(
            "Wrp session close lecture_id=%s pcm_chunks=%d feed_failures=%d",
            self.lecture_id,
            len(self.audio_chunks_sent),
            self._feed_fail_count,
        )
        self._feeding = False
        self._message_queue.put(None)
        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=5.0)
        self._worker = None
        self._wrp.disconnect()

    def _enqueue_finalized(self, raw: str) -> None:
        self._message_queue.put(raw)

    def _run_message_worker(self) -> None:
        while True:
            item = self._message_queue.get()
            try:
                if item is None:
                    break
                handler = self._handler
                if handler is not None:
                    logger.debug(
                        "Delivering finalized JSON to bridge len=%d",
                        len(item),
                    )
                    handler(item)
            finally:
                self._message_queue.task_done()


@dataclass(frozen=True, slots=True)
class WrpAmiVoiceSessionFactory:
    ws_url: str = DEFAULT_WS_URL
    proxy_server_name: str | None = None
    grammar_file_names: str = DEFAULT_GRAMMAR_FILE_NAMES
    receive_timeout_ms: int = _RECEIVE_TIMEOUT_MS

    def create(self, *, api_key: str, lecture_id: str) -> WrpAmiVoiceSession:
        return WrpAmiVoiceSession(
            lecture_id=lecture_id,
            api_key=api_key,
            ws_url=self.ws_url,
            proxy_server_name=self.proxy_server_name,
            grammar_file_names=self.grammar_file_names,
            receive_timeout_ms=self.receive_timeout_ms,
        )
