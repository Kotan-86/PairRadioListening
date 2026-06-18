# 仕様: docs/spec/framework_amivoice.md#4.3
from __future__ import annotations

import numpy as np
import pytest

from framework.amivoice.audio_capture_source import resolve_input_device_index
from framework.amivoice.pcm_resample import (
    TARGET_SAMPLE_RATE,
    pcm_bytes_to_mono_int16,
    resample_mono_int16,
    to_16k_mono_pcm_bytes,
)


@pytest.mark.phase1c
def test_capture_resamples_to_16k_mono() -> None:
    src_rate = 48_000
    duration_sec = 0.1
    sample_count = int(src_rate * duration_sec)
    stereo = np.zeros((sample_count, 2), dtype=np.int16)
    stereo[:, 0] = np.arange(sample_count, dtype=np.int16) % 1000
    stereo[:, 1] = stereo[:, 0]
    pcm_in = stereo.tobytes()

    out = to_16k_mono_pcm_bytes(pcm_in, sample_rate=src_rate, channels=2)
    mono = np.frombuffer(out, dtype=np.int16)
    expected_len = int(round(sample_count * TARGET_SAMPLE_RATE / src_rate))
    assert len(mono) == expected_len
    assert mono[0] == stereo[0, 0]


@pytest.mark.phase1c
def test_pcm_bytes_to_mono_from_stereo() -> None:
    samples = np.array([100, 200, 300, 400], dtype=np.int16)
    mono = pcm_bytes_to_mono_int16(samples.tobytes(), channels=2)
    assert mono.tolist() == [100, 300]


@pytest.mark.phase1c
def test_pcm_bytes_to_mono_keeps_signal_when_stereo_is_antiphase() -> None:
    stereo = np.array([1000, -1000, 2000, -2000], dtype=np.int16)
    mono = pcm_bytes_to_mono_int16(stereo.tobytes(), channels=2)
    assert mono.tolist() == [1000, 2000]


@pytest.mark.phase1c
def test_resolve_input_device_finds_vb_cable_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = [
        {"name": "Built-in Microphone", "max_input_channels": 1},
        {"name": "VB-Cable, Core Audio (2 in, 2 out)", "max_input_channels": 2},
    ]
    import sounddevice as sd

    monkeypatch.setattr(sd, "query_devices", lambda: devices)
    assert resolve_input_device_index(None) == 1


@pytest.mark.phase1c
def test_resolve_input_device_honors_audio_capture_device_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    devices = [
        {"name": "VB-Cable, Core Audio (2 in, 2 out)", "max_input_channels": 2},
        {"name": "Other Mic", "max_input_channels": 1},
    ]
    import sounddevice as sd

    monkeypatch.setattr(sd, "query_devices", lambda: devices)
    assert resolve_input_device_index("VB-Cable") == 0


@pytest.mark.phase1c
def test_resample_mono_boundary_empty() -> None:
    empty = np.array([], dtype=np.int16)
    assert resample_mono_int16(empty, src_rate=48_000).size == 0
