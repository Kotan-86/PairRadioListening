# 仕様: docs/spec/framework.md#1.4
from __future__ import annotations

import logging
import sys

from framework.settings import Settings, load_settings

_CONFIGURED = False


def configure_logging(settings: Settings | None = None) -> None:
    """アプリ起動時に 1 回だけ呼ぶ。AMIVOICE_DEBUG で framework.amivoice を DEBUG にする。"""
    global _CONFIGURED
    if _CONFIGURED:
        return
    settings = settings or load_settings()
    root_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=root_level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )
    if settings.amivoice_debug:
        logging.getLogger("framework.amivoice").setLevel(logging.DEBUG)
        logging.debug("AmiVoice debug logging enabled (AMIVOICE_DEBUG)")
    _CONFIGURED = True
