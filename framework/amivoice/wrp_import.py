# 仕様: docs/spec/framework_amivoice.md#4.2
"""Vendor 同梱 Wrp を 1 回だけ sys.path に載せて import する。"""
from __future__ import annotations

import sys
from pathlib import Path

_VENDOR_SRC = Path(__file__).resolve().parents[2] / "third_party" / "amivoice_wrp" / "src"
_VENDOR_SRC_STR = str(_VENDOR_SRC)
if _VENDOR_SRC_STR not in sys.path:
    sys.path.insert(0, _VENDOR_SRC_STR)

from com.amivoice.wrp.Wrp import Wrp  # noqa: E402
from com.amivoice.wrp.WrpListener import WrpListener  # noqa: E402

__all__ = ["Wrp", "WrpListener"]
