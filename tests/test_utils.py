from __future__ import annotations

from unittest import TestCase

from pytoniq_core import Cell
from tonutils.types import NetworkGlobalID

from ton_mcp.utils.comment import serialize_comment
from ton_mcp.utils.content import (
    _extract_onchain_fields,  # noqa
    _is_ipfs_uri,  # noqa
    _normalize_uri,  # noqa
)
from ton_mcp.utils.urls import explorer_url, make_qr_url


class TestNormalizeUri(TestCase):
    """IPFS URI → HTTP gateway conversion."""

    def test_ipfs_scheme_converted(self) -> None:
        result = _normalize_uri("ipfs://QmHash123/metadata.json")
        self.assertEqual(
            result,
            "https://ipfs.io/ipfs/QmHash123/metadata.json",
        )

    def test_http_unchanged(self) -> None:
        url = "https://example.com/meta.json"
        self.assertEqual(_normalize_uri(url), url)

    def test_ipfs_strips_prefix_correctly(self) -> None:
        result = _normalize_uri("ipfs://bafyabc")
        self.assertFalse(result.startswith("ipfs://"))
        self.assertTrue(result.startswith("https://"))


class TestIsIpfsUri(TestCase):
    """Detect IPFS URIs by scheme or path."""

    def test_ipfs_scheme(self) -> None:
        self.assertTrue(_is_ipfs_uri("ipfs://QmHash"))

    def test_gateway_url(self) -> None:
        self.assertTrue(_is_ipfs_uri("https://ipfs.io/ipfs/QmHash"))

    def test_regular_https(self) -> None:
        self.assertFalse(_is_ipfs_uri("https://example.com/meta"))

    def test_cloudflare_gateway(self) -> None:
        self.assertTrue(_is_ipfs_uri("https://cloudflare-ipfs.com/ipfs/QmHash"))


class TestExtractOnchainFields(TestCase):
    """Filter string fields from OnchainContent metadata."""

    def test_filters_non_string_keys(self) -> None:
        from unittest.mock import MagicMock

        content = MagicMock()
        content.metadata = {
            "name": "Token",
            "symbol": "TKN",
            123: "numeric_key",
            "image": "https://img.png",
        }
        result = _extract_onchain_fields(content)
        self.assertEqual(
            result,
            {
                "name": "Token",
                "symbol": "TKN",
                "image": "https://img.png",
            },
        )
        self.assertNotIn(123, result)

    def test_filters_non_string_values(self) -> None:
        from unittest.mock import MagicMock

        content = MagicMock()
        content.metadata = {
            "name": "Token",
            "decimals": 9,
            "count": 42,
        }
        result = _extract_onchain_fields(content)
        self.assertEqual(result, {"name": "Token"})


class TestSerializeComment(TestCase):
    """Comment serialization edge cases."""

    def test_empty_returns_none(self) -> None:
        self.assertIsNone(serialize_comment(""))
        self.assertIsNone(serialize_comment(None))

    def test_different_texts_different_hashes(self) -> None:
        a = serialize_comment("payment for services")
        b = serialize_comment("refund")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertNotEqual(a.hash, b.hash)

    def test_same_text_same_hash(self) -> None:
        a = serialize_comment("hello")
        b = serialize_comment("hello")
        self.assertEqual(a.hash, b.hash)

    def test_unicode_text(self) -> None:
        result = serialize_comment("Оплата за услуги 🎉")
        self.assertIsInstance(result, Cell)


class TestExplorerUrl(TestCase):
    """Explorer URL generation per network/explorer."""

    TX = "abcdef1234567890"

    def test_mainnet_tonviewer(self) -> None:
        url = explorer_url(NetworkGlobalID.MAINNET, self.TX, "tonviewer")
        self.assertEqual(url, f"https://tonviewer.com/transaction/{self.TX}")

    def test_mainnet_tonscan(self) -> None:
        url = explorer_url(NetworkGlobalID.MAINNET, self.TX, "tonscan")
        self.assertEqual(url, f"https://tonscan.org/tx/{self.TX}")

    def test_testnet_prefix(self) -> None:
        url = explorer_url(NetworkGlobalID.TESTNET, self.TX, "tonviewer")
        self.assertIn("testnet.", url)

    def test_tetra_prefix(self) -> None:
        url = explorer_url(NetworkGlobalID.TETRA, self.TX, "tonviewer")
        self.assertIn("tetra.", url)

    def test_unknown_explorer_falls_back_to_tonviewer(self) -> None:
        url = explorer_url(NetworkGlobalID.MAINNET, self.TX, "nonexistent")
        self.assertIn("tonviewer.com", url)


class TestMakeQrUrl(TestCase):
    """QR code URL encoding."""

    def test_encodes_connect_url_as_base64(self) -> None:
        import base64

        connect_url = "tc://some-long-connect-url?key=value"
        url = make_qr_url(connect_url)
        expected = base64.b64encode(connect_url.encode()).decode()
        self.assertIn(f"data={expected}", url)
