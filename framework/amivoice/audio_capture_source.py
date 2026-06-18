# 仕様: docs/spec/framework_amivoice.md#4.3
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from framework.amivoice.pcm_resample import TARGET_SAMPLE_RATE, to_16k_mono_pcm_bytes

logger = logging.getLogger(__name__)

# macOS Core Audio では "VB-Cable, Core Audio (2 in, 2 out)" 等。Windows は CABLE Output。
DEFAULT_DEVICE_HINTS = ("VB-Cable", "CABLE Output", "CABLE OUTPUT")


class AudioCaptureSource(Protocol):
    def start(self, on_pcm: Callable[[bytes], None]) -> None: ...

    def stop(self) -> None: ...


def resolve_input_device_index(
    device_name: str | None,
    *,
    hints: tuple[str, ...] = DEFAULT_DEVICE_HINTS,
) -> int | None:
    import sounddevice as sd

    devices = sd.query_devices()
    if device_name:
        target = device_name.strip().lower()
        for index, info in enumerate(devices):
            if info["max_input_channels"] > 0 and target in str(info["name"]).lower():
                return index
        logger.warning("AUDIO_CAPTURE_DEVICE not found: %s", device_name)

    for hint in hints:
        needle = hint.lower()
        for index, info in enumerate(devices):
            if info["max_input_channels"] > 0 and needle in str(info["name"]).lower():
                logger.info("Using audio capture device: %s", info["name"])
                return index
    return None


@dataclass
class SoundDeviceAudioCaptureSource:
    """VB-Cable 等の入力端子から PCM を読み、16 kHz mono に整形してコールバックする。"""

    device_name: str | None = None
    block_duration_ms: int = 100
    _on_pcm: Callable[[bytes], None] | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self, on_pcm: Callable[[bytes], None]) -> None:
        self.stop()
        logger.debug("Audio capture start device_name=%r", self.device_name)
        self._on_pcm = on_pcm
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_capture,
            name="audio-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        logger.debug("Audio capture stop")
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        self._thread = None
        self._on_pcm = None

    def _run_capture(self) -> None:
        import sounddevice as sd

        device_index = resolve_input_device_index(self.device_name)
        if device_index is None:
            logger.error(
                "No capture device found. Set AUDIO_CAPTURE_DEVICE or install VB-Cable."
            )
            return

        info = sd.query_devices(device_index)
        sample_rate = int(info["default_samplerate"])
        channels = min(int(info["max_input_channels"]), 2)
        block_size = max(1, int(sample_rate * self.block_duration_ms / 1000))
        logger.debug(
            "Audio capture stream device=%r index=%s rate=%s channels=%s block=%s",
            info["name"],
            device_index,
            sample_rate,
            channels,
            block_size,
        )

        def callback(indata, _frames, _time, status) -> None:
            if status:
                logger.debug("sounddevice status: %s", status)
            if self._stop_event.is_set() or self._on_pcm is None:
                return
            pcm = bytes(indata)
            out = to_16k_mono_pcm_bytes(
                pcm,
                sample_rate=sample_rate,
                channels=channels,
            )
            if out:
                self._on_pcm(out)

        try:
            with sd.RawInputStream(
                device=device_index,
                channels=channels,
                samplerate=sample_rate,
                dtype="int16",
                blocksize=block_size,
                callback=callback,
            ):
                while not self._stop_event.is_set():
                    self._stop_event.wait(timeout=0.1)
        except Exception:
            logger.exception("Audio capture failed")


@dataclass
class FakeAudioCaptureSource:
    """テスト用: 事前登録した PCM チャンクをキャプチャスレッド相当で送出する。"""

    chunks: list[bytes] = field(default_factory=list)
    chunk_interval_sec: float = 0.0
    started: bool = field(default=False, init=False)
    _on_pcm: Callable[[bytes], None] | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self, on_pcm: Callable[[bytes], None]) -> None:
        self.stop()
        self._on_pcm = on_pcm
        self._stop_event.clear()
        self.started = True
        self._thread = threading.Thread(
            target=self._emit_chunks,
            name="fake-audio-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        self._thread = None
        self._on_pcm = None
        self.started = False

    def _emit_chunks(self) -> None:
        import time

        for chunk in self.chunks:
            if self._stop_event.is_set() or self._on_pcm is None:
                break
            self._on_pcm(chunk)
            if self.chunk_interval_sec > 0:
                time.sleep(self.chunk_interval_sec)
