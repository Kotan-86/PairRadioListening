# 仕様: docs/spec/domain.md#audio_data
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioData:
    storage_url: str | None = None
    content_type: str | None = None

    def __post_init__(self) -> None:
        if self.storage_url is not None and not self.storage_url.strip():
            raise ValueError("audio_data の storage_url は空文字にできません")
        if self.content_type is not None and not self.content_type.strip():
            raise ValueError("audio_data の content_type は空文字にできません")
        if self.storage_url is None and self.content_type is not None:
            raise ValueError(
                "audio_data で content_type を指定する場合は storage_url も必要です"
            )

    @classmethod
    def empty(cls) -> "AudioData":
        return cls()
