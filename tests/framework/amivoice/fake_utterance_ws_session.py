# 仕様: docs/spec/framework_amivoice.md#4.8（Bridge E2E 用スタブ）
from __future__ import annotations

import json
from dataclasses import dataclass, field

from framework.amivoice.null_ws_session import NullAmiVoiceWsSession


@dataclass
class UtteranceEmittingWsSession(NullAmiVoiceWsSession):
    """PCM 送信時に確定 JSON を 1 回だけ handler へ渡す。"""

    utterance_json: str = ""
    _emitted: bool = field(default=False, init=False)

    def send_audio(self, pcm_bytes: bytes) -> None:
        super().send_audio(pcm_bytes)
        if self._emitted or not pcm_bytes or self._handler is None:
            return
        if self.utterance_json:
            self._handler(self.utterance_json)
            self._emitted = True


@dataclass(frozen=True, slots=True)
class UtteranceEmittingWsSessionFactory:
    utterance_payload: dict

    def create(self, *, api_key: str, lecture_id: str) -> UtteranceEmittingWsSession:
        _ = api_key
        return UtteranceEmittingWsSession(
            lecture_id=lecture_id,
            utterance_json=json.dumps(self.utterance_payload),
        )
