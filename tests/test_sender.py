from __future__ import annotations

import typing as t
from dataclasses import dataclass
from unittest import TestCase

from ton_mcp.constants import GAS_RESERVE
from ton_mcp.core.sender import Sender, format_send_result
from ton_mcp.types import SendMessage, SendResult


@dataclass
class FakeContractInfo:
    """Minimal mock for ContractInfo used by _check_balance."""

    balance: int
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None


class TestCheckBalance(TestCase):
    """Sender._check_balance — validates wallet has enough funds."""

    ADDR = "UQtest"

    def test_sufficient_balance_passes(self) -> None:
        msgs = [SendMessage(
            destination="0:0" + "0" * 63,
            amount=500_000_000,
        )]
        info = FakeContractInfo(
            balance=500_000_000 + GAS_RESERVE + 1,
        )
        Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]

    def test_insufficient_balance_raises(self) -> None:
        msgs = [SendMessage(
            destination="0:0" + "0" * 63,
            amount=1_000_000_000,
        )]
        info = FakeContractInfo(balance=500_000_000)
        with self.assertRaises(ValueError) as ctx:
            Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]
        self.assertIn("Insufficient balance", str(ctx.exception))
        self.assertIn(self.ADDR, str(ctx.exception))

    def test_zero_amount_skips_check(self) -> None:
        msgs = [SendMessage(
            destination="0:0" + "0" * 63,
            amount=0,
        )]
        info = FakeContractInfo(balance=0)
        Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]

    def test_empty_messages_skips_check(self) -> None:
        info = FakeContractInfo(balance=0)
        Sender._check_balance(info, [], self.ADDR)  # type: ignore[arg-type]

    def test_multiple_messages_summed(self) -> None:
        dest = "0:0" + "0" * 63
        msgs = [
            SendMessage(destination=dest, amount=300_000_000),
            SendMessage(destination=dest, amount=400_000_000),
        ]
        info = FakeContractInfo(balance=600_000_000)
        with self.assertRaises(ValueError):
            Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]

    def test_exact_balance_with_reserve_passes(self) -> None:
        dest = "0:0" + "0" * 63
        amount = 500_000_000
        msgs = [SendMessage(destination=dest, amount=amount)]
        info = FakeContractInfo(balance=amount + GAS_RESERVE)
        Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]

    def test_one_nano_short_raises(self) -> None:
        dest = "0:0" + "0" * 63
        amount = 500_000_000
        msgs = [SendMessage(destination=dest, amount=amount)]
        info = FakeContractInfo(balance=amount + GAS_RESERVE - 1)
        with self.assertRaises(ValueError):
            Sender._check_balance(info, msgs, self.ADDR)  # type: ignore[arg-type]


class TestFormatSendResult(TestCase):
    """format_send_result — builds TransactionResult from SendResult."""

    def test_fields_mapped_correctly(self) -> None:
        sr = SendResult(
            normalized_hash="deadbeef",
            explorer_url="https://tonviewer.com/transaction/deadbeef",
        )
        result = format_send_result("TON transfer", 3, sr)
        self.assertEqual(result.status, "confirmed")
        self.assertEqual(result.hash, "deadbeef")
        self.assertEqual(result.label, "TON transfer")
        self.assertEqual(result.messages, 3)
        self.assertIn("tonviewer.com", result.explorer)
