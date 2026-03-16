from __future__ import annotations

from unittest import TestCase

from pydantic import ValidationError

from ton_mcp.models import (
    JettonTransfer,
    NFTInfoResult,
    RawMessage,
    TonTransfer,
    TransactionResult,
)


class TestTonTransferValidation(TestCase):
    """TonTransfer — required fields and defaults."""

    def test_missing_destination_raises(self) -> None:
        with self.assertRaises(ValidationError):
            TonTransfer(amount="1.0")  # type: ignore[call-arg]

    def test_missing_amount_raises(self) -> None:
        with self.assertRaises(ValidationError):
            TonTransfer(destination="UQaddr")  # type: ignore[call-arg]


class TestJettonTransferDecimals(TestCase):
    """JettonTransfer.decimals — the silent footgun."""

    def test_default_decimals_is_9(self) -> None:
        jt = JettonTransfer(
            destination="UQaddr",
            jetton_master_address="EQmaster",
            amount="100",
        )
        self.assertEqual(jt.decimals, 9)

    def test_usdt_decimals_6(self) -> None:
        jt = JettonTransfer(
            destination="UQaddr",
            jetton_master_address="EQmaster",
            amount="100",
            decimals=6,
        )
        self.assertEqual(jt.decimals, 6)


class TestRawMessageAmountFormat(TestCase):
    """RawMessage.amount — string nanotons, not human-readable."""

    def test_amount_is_string(self) -> None:
        rm = RawMessage(
            destination="EQaddr",
            amount="500000000",
        )
        self.assertEqual(rm.amount, "500000000")

    def test_body_defaults_to_none(self) -> None:
        rm = RawMessage(
            destination="EQaddr",
            amount="100000000",
        )
        self.assertIsNone(rm.body)


class TestNFTInfoResultSBTFields(TestCase):
    """NFTInfoResult — SBT fields for soulbound tokens."""

    def test_sbt_fields_default_to_none(self) -> None:
        nft = NFTInfoResult(
            address="EQaddr",
            initialized=True,
            index=0,
        )
        self.assertIsNone(nft.authority_address)
        self.assertIsNone(nft.revoked_at)

    def test_sbt_fields_populated(self) -> None:
        nft = NFTInfoResult(
            address="EQaddr",
            initialized=True,
            index=5,
            authority_address="UQauthority",
            revoked_at=0,
        )
        self.assertEqual(nft.authority_address, "UQauthority")
        self.assertEqual(nft.revoked_at, 0)

    def test_revoked_sbt(self) -> None:
        nft = NFTInfoResult(
            address="EQaddr",
            initialized=True,
            index=5,
            authority_address="UQauth",
            revoked_at=1700000000,
        )
        self.assertGreater(nft.revoked_at, 0)


class TestTransactionResultSerialization(TestCase):
    """TransactionResult — JSON output correctness."""

    def test_model_dump_has_all_fields(self) -> None:
        r = TransactionResult(
            status="confirmed",
            hash="abc",
            explorer="https://tonviewer.com/transaction/abc",
            label="TON transfer",
            messages=2,
        )
        data = r.model_dump()
        self.assertIn("status", data)
        self.assertIn("hash", data)
        self.assertIn("explorer", data)
        self.assertIn("label", data)
        self.assertIn("messages", data)
        self.assertIn("hint", data)
        self.assertIsNone(data["hint"])

    def test_hint_propagated_from_base(self) -> None:
        r = TransactionResult(
            status="confirmed",
            hash="x",
            explorer="url",
            label="test",
            messages=1,
            hint="check explorer for details",
        )
        self.assertEqual(r.hint, "check explorer for details")
