# 仕様: docs/spec/interface.md#6.5 / §1.3
from interface_adapters.presentation.error_messages import (
    QUOTE_EXCERPT_MAX_LENGTH,
    QUOTE_LABEL_SEPARATOR,
)


def format_quote_label(speaker_label: str, excerpt: str) -> str:
    text = excerpt
    if len(text) > QUOTE_EXCERPT_MAX_LENGTH:
        text = text[:QUOTE_EXCERPT_MAX_LENGTH] + "…"
    return f"{speaker_label}{QUOTE_LABEL_SEPARATOR}{text}"
