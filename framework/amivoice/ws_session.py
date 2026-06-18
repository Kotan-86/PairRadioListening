# 仕様: docs/spec/framework_amivoice.md#4.2
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class AmiVoiceWsSession(Protocol):
    def send_start_command(self, command: str) -> None: ...

    def send_end_command(self, command: str) -> None: ...

    def send_audio(self, pcm_bytes: bytes) -> None: ...

    def set_message_handler(self, handler: Callable[[str], None]) -> None: ...

    def close(self) -> None: ...


class AmiVoiceWsSessionFactory(Protocol):
    def create(self, *, api_key: str, lecture_id: str) -> AmiVoiceWsSession: ...
