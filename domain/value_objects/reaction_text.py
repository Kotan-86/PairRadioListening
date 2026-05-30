# 仕様: docs/spec/domain.md#reaction_text
from dataclasses import dataclass


@dataclass(frozen=True)
class ReactionText:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("reaction_text の text は空にできません")
