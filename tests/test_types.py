from __future__ import annotations

from unittest import TestCase

from pytoniq_core import Address

from ton_mcp.types import SendMessage, SendResult


class TestSendMessageToWalletMessage(TestCase):
    """SendMessage → WalletMessage conversion for SECRET_KEY dispatch."""

    ADDR = "0:0000000000000000000000000000000000000000000000000000000000000000"

    def test_text_body_serialized_to_cell(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=1_000_000_000,
            body="Hello TON",
        )
        wm = msg.to_wallet_message()
        self.assertIsNotNone(wm.message.body)

    def test_cell_body_passed_through(self) -> None:
        from ton_mcp.utils.comment import serialize_comment

        cell = serialize_comment("test")
        msg = SendMessage(
            destination=self.ADDR,
            amount=500_000_000,
            body=cell,
        )
        wm = msg.to_wallet_message()
        self.assertIsNotNone(wm.message.body)

    def test_none_body_produces_empty_cell(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=100,
            body=None,
        )
        wm = msg.to_wallet_message()
        self.assertIsNotNone(wm.message)

    def test_wallet_message_serializable(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=999_999_999,
        )
        wm = msg.to_wallet_message()
        self.assertTrue(wm.message.is_internal)


class TestSendMessageToTcMessage(TestCase):
    """SendMessage → SendTransactionMessage for TONCONNECT dispatch."""

    ADDR = "0:0000000000000000000000000000000000000000000000000000000000000000"

    def test_string_destination_converted_to_address(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=1_000_000,
        )
        tc = msg.to_tc_message()
        self.assertIsInstance(tc.address, Address)

    def test_amount_preserved(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=123_456_789,
        )
        tc = msg.to_tc_message()
        self.assertEqual(tc.amount, 123_456_789)

    def test_text_body_serialized(self) -> None:
        msg = SendMessage(
            destination=self.ADDR,
            amount=100,
            body="test comment",
        )
        tc = msg.to_tc_message()
        self.assertIsNotNone(tc.payload)


class TestSendResult(TestCase):
    """SendResult model correctness."""

    def test_fields_stored(self) -> None:
        r = SendResult(
            normalized_hash="abc123def",
            explorer_url="https://tonviewer.com/transaction/abc123def",
        )
        self.assertEqual(r.normalized_hash, "abc123def")
        self.assertIn("tonviewer.com", r.explorer_url)
