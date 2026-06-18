# 仕様: docs/spec/framework_amivoice.md#4.2（API キー未設定・テスト用スタブ）
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class NullAmiVoiceWsSession:
    lecture_id: str
    commands: list[str] = field(default_factory=list)
    audio_chunks: list[bytes] = field(default_factory=list)
    _handler: Callable[[str], None] | None = None

    def send_start_command(self, command: str) -> None:
        self.commands.append(command)

    def send_end_command(self, command: str) -> None:
        self.commands.append(command)

    def send_audio(self, pcm_bytes: bytes) -> None:
        self.audio_chunks.append(pcm_bytes)

    def set_message_handler(self, handler: Callable[[str], None]) -> None:
        self._handler = handler

    def close(self) -> None:
        pass

    def deliver_message(self, raw: str) -> None:
        if self._handler is not None:
            self._handler(raw)


@dataclass(frozen=True, slots=True)
class NullAmiVoiceWsSessionFactory:
    """WebSocket 接続なし。start/end コマンド記録とテスト用メッセージ注入のみ。"""

    def create(self, *, api_key: str, lecture_id: str) -> NullAmiVoiceWsSession:
        _ = api_key
        return NullAmiVoiceWsSession(lecture_id=lecture_id)
