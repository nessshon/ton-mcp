from __future__ import annotations

import typing as t
from unittest import TestCase
from unittest.mock import MagicMock

from pytoniq_core import Address

from ton_mcp.utils.account import safe_address


class TestSafeAddress(TestCase):
    """safe_address — graceful address conversion."""

    def test_none_returns_none(self) -> None:
        self.assertIsNone(safe_address(None))

    def test_valid_address_returns_string(self) -> None:
        addr = Address(
            "0:0000000000000000000000000000000000000000000000000000000000000000"
        )
        result = safe_address(addr)
        self.assertIsInstance(result, str)
        self.assertTrue(
            result.startswith("UQ") or result.startswith("EQ")
            or result.startswith("0:")
        )

    def test_bounceable_format(self) -> None:
        addr = Address(
            "0:0000000000000000000000000000000000000000000000000000000000000000"
        )
        bounceable = safe_address(addr, is_bounceable=True)
        non_bounceable = safe_address(addr, is_bounceable=False)
        self.assertNotEqual(bounceable, non_bounceable)

    def test_broken_object_returns_none(self) -> None:
        broken = MagicMock()
        broken.to_str.side_effect = AttributeError("no method")
        self.assertIsNone(safe_address(broken))

    def test_slice_like_object_returns_none(self) -> None:
        obj = MagicMock()
        obj.to_str.side_effect = Exception("not an address")
        self.assertIsNone(safe_address(obj))
