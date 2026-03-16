from __future__ import annotations

from unittest import TestCase

from tonutils.types import NetworkGlobalID

from ton_mcp.core.config import Config
from ton_mcp.types import SignMethod


class TestSignMethodDetection(TestCase):
    """Config.sign_method — SECRET_KEY vs TONCONNECT routing."""

    def test_no_secret_means_tonconnect(self) -> None:
        cfg = Config(
            wallet_secret=None,
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertEqual(cfg.sign_method, SignMethod.TONCONNECT)

    def test_hex_key_means_secret_key(self) -> None:
        cfg = Config(
            wallet_secret="ab" * 32,
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertEqual(cfg.sign_method, SignMethod.SECRET_KEY)

    def test_mnemonic_means_secret_key(self) -> None:
        words = " ".join(["word"] * 24)
        cfg = Config(
            wallet_secret=words,
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertEqual(cfg.sign_method, SignMethod.SECRET_KEY)


class TestIsMnemonic(TestCase):
    """Config.is_mnemonic — distinguishing mnemonic from hex key."""

    def test_spaces_means_mnemonic(self) -> None:
        cfg = Config(
            wallet_secret="abandon ability able about",
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertTrue(cfg.is_mnemonic)

    def test_hex_not_mnemonic(self) -> None:
        cfg = Config(
            wallet_secret="deadbeef" * 8,
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertFalse(cfg.is_mnemonic)

    def test_empty_secret_not_mnemonic(self) -> None:
        cfg = Config(
            wallet_secret=None,
            network="mainnet",
            _env_file=None,  # type: ignore[call-arg]
        )
        self.assertFalse(cfg.is_mnemonic)


class TestNetworkParsing(TestCase):
    """Network string → NetworkGlobalID enum."""

    def test_known_networks(self) -> None:
        cases = {
            "mainnet": NetworkGlobalID.MAINNET,
            "testnet": NetworkGlobalID.TESTNET,
            "tetra": NetworkGlobalID.TETRA,
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(Config._parse_network_str(name), expected)

    def test_case_insensitive(self) -> None:
        self.assertEqual(
            Config._parse_network_str("TESTNET"),
            NetworkGlobalID.TESTNET,
        )

    def test_unknown_network_raises(self) -> None:
        with self.assertRaises(ValueError):
            Config._parse_network_str("devnet")


class TestNetworkProviderValidation(TestCase):
    """Config rejects unsupported provider/explorer combos."""

    def test_lite_on_tetra_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Config(
                network="tetra",
                client_provider="lite",
                _env_file=None,  # type: ignore[call-arg]
            )

    def test_tonscan_on_tetra_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Config(
                network="tetra",
                explorer="tonscan",
                _env_file=None,  # type: ignore[call-arg]
            )

    def test_unknown_explorer_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Config(
                network="mainnet",
                explorer="etherscan",
                _env_file=None,  # type: ignore[call-arg]
            )
