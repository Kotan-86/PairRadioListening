# 仕様: docs/spec/framework_amivoice.md#3.1, §4.3
from __future__ import annotations

import numpy as np

TARGET_SAMPLE_RATE = 16_000


def pcm_bytes_to_mono_int16(pcm_bytes: bytes, *, channels: int) -> np.ndarray:
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    if channels <= 1:
        return samples.copy()
    if len(samples) % channels != 0:
        samples = samples[: len(samples) - (len(samples) % channels)]
    framed = samples.reshape(-1, channels)
    # Stereo downmix by channel-average can cancel to silence on anti-phase inputs.
    # Prefer first channel to keep stable amplitude for recognition input.
    return framed[:, 0].astype(np.int16)


def resample_mono_int16(
    samples: np.ndarray,
    *,
    src_rate: int,
    dst_rate: int = TARGET_SAMPLE_RATE,
) -> np.ndarray:
    if src_rate == dst_rate:
        return samples
    if len(samples) == 0:
        return samples
    dst_length = int(round(len(samples) * dst_rate / src_rate))
    if dst_length == 0:
        return np.array([], dtype=np.int16)
    x_old = np.arange(len(samples), dtype=np.float64)
    x_new = np.linspace(0, len(samples) - 1, num=dst_length)
    resampled = np.interp(x_new, x_old, samples.astype(np.float64))
    return np.clip(resampled, -32768, 32767).astype(np.int16)


def to_16k_mono_pcm_bytes(
    pcm_bytes: bytes,
    *,
    sample_rate: int,
    channels: int,
) -> bytes:
    mono = pcm_bytes_to_mono_int16(pcm_bytes, channels=channels)
    resampled = resample_mono_int16(mono, src_rate=sample_rate)
    return resampled.tobytes()
