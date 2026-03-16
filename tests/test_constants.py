from __future__ import annotations

from unittest import TestCase

from tonutils.utils import to_nano

from ton_mcp.constants import (
    FORWARD_NOTIFY,
    GAS_MINT_JETTON,
    GAS_MINT_NFT,
    GAS_RESERVE,
    GAS_TRANSFER,
)


class TestGasConstantsValues(TestCase):
    """Gas constants match expected TON amounts."""

    def test_gas_reserve_is_01_ton(self) -> None:
        self.assertEqual(GAS_RESERVE, to_nano("0.1"))

    def test_gas_transfer_is_005_ton(self) -> None:
        self.assertEqual(GAS_TRANSFER, to_nano("0.05"))

    def test_gas_mint_nft_is_0025_ton(self) -> None:
        self.assertEqual(GAS_MINT_NFT, to_nano("0.025"))

    def test_gas_mint_jetton_is_0125_ton(self) -> None:
        self.assertEqual(GAS_MINT_JETTON, to_nano("0.125"))

    def test_forward_notify_is_1_nanoton(self) -> None:
        self.assertEqual(FORWARD_NOTIFY, 1)

    def test_ordering_transfer_lt_reserve(self) -> None:
        self.assertLess(GAS_TRANSFER, GAS_RESERVE)

    def test_ordering_mint_nft_lt_transfer(self) -> None:
        self.assertLess(GAS_MINT_NFT, GAS_TRANSFER)
