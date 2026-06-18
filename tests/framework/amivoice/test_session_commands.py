# 仕様: docs/spec/framework_amivoice.md#3.1
from __future__ import annotations

import pytest

from framework.amivoice.session_commands import (
    DEFAULT_GRAMMAR_FILE_NAMES,
    amivoice_start_command,
)


@pytest.mark.phase1c
def test_default_grammar_is_a2_ja_general() -> None:
    assert DEFAULT_GRAMMAR_FILE_NAMES == "-a2-ja-general"


@pytest.mark.phase1c
def test_amivoice_start_command_includes_grammar() -> None:
    assert amivoice_start_command() == "s LSB16K -a2-ja-general"
    assert amivoice_start_command("-custom-engine") == "s LSB16K -custom-engine"
