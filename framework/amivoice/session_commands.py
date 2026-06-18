# 仕様: docs/spec/framework_amivoice.md#3.1, docs/spec/framework_amivoice.md#4.2
from __future__ import annotations

DEFAULT_CODEC = "LSB16K"
DEFAULT_GRAMMAR_FILE_NAMES = "-a2-ja-general"


def amivoice_start_command(
    grammar_file_names: str = DEFAULT_GRAMMAR_FILE_NAMES,
    *,
    codec: str = DEFAULT_CODEC,
) -> str:
    """Bridge が渡す開始コマンド文字列（Wrp は setter で同等の設定を行う）。"""
    return f"s {codec} {grammar_file_names}"
