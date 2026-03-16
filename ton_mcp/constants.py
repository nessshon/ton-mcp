from __future__ import annotations

import typing as t
from pathlib import Path

from tonutils.contracts import (
    WalletV3R1,
    WalletV3R2,
    WalletV4R1,
    WalletV4R2,
    WalletV5R1,
    WalletHighloadV3R1,
    WalletPreprocessedV2,
)
from tonutils.contracts.wallet import BaseWallet
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

from ton_mcp.types import NetworkCapabilities

GAS_RESERVE: t.Final[int] = to_nano("0.1")
"""Conservative gas reserve covering typical fees for transfers."""

GAS_TRANSFER: t.Final[int] = to_nano("0.05")
"""Gas attached to jetton/NFT transfer messages."""

GAS_MINT_NFT: t.Final[int] = to_nano("0.025")
"""Gas attached to NFT mint messages."""

GAS_MINT_JETTON: t.Final[int] = to_nano("0.125")
"""Gas attached to jetton mint messages."""

FORWARD_MINT_NFT: t.Final[int] = to_nano("0.01")
"""Forward amount for NFT mint."""

FORWARD_MINT_JETTON: t.Final[int] = to_nano("0.1")
"""Forward amount for jetton mint."""

FORWARD_NOTIFY: t.Final[int] = 1
"""Minimal forward amount (1 nanoton) for transfer notifications."""

INSTRUCTIONS_PATH: str = str(Path(__file__).parent / "instructions.md")
"""Absolute path to the instructions.md file bundled with the package."""

with open(INSTRUCTIONS_PATH, encoding="utf-8") as _f:
    INSTRUCTIONS: str = _f.read()
"""System prompt text loaded from instructions.md, injected into MCP server instructions."""

INCLUDE_WALLETS = ["telegram-wallet", "tonkeeper", "mytonwallet", "tonhub"]
"""TonConnect wallet app IDs to offer during connection (popular TON wallets)."""

TONCONNECT_SESSION_KEY = "ton-mcp"
"""TonConnect session key for connector lookup."""

WALLET_VERSIONS: t.Final[t.Dict[str, t.Type[BaseWallet]]] = {
    "v3r1": WalletV3R1,
    "v3r2": WalletV3R2,
    "v4r1": WalletV4R1,
    "v4r2": WalletV4R2,
    "v5r1": WalletV5R1,
    "highload_v3r1": WalletHighloadV3R1,
    "preprocessed_v2": WalletPreprocessedV2,
}
"""Mapping of wallet version short names to their tonutils contract classes."""

NETWORK_CAPABILITIES: t.Final[t.Dict[NetworkGlobalID, NetworkCapabilities]] = {
    NetworkGlobalID.MAINNET: NetworkCapabilities(
        supported_providers=frozenset({"toncenter", "tonapi", "lite"}),
        supported_explorers=frozenset({"tonviewer", "tonscan"}),
    ),
    NetworkGlobalID.TESTNET: NetworkCapabilities(
        supported_providers=frozenset({"toncenter", "tonapi", "lite"}),
        supported_explorers=frozenset({"tonviewer", "tonscan"}),
    ),
    NetworkGlobalID.TETRA: NetworkCapabilities(
        supported_providers=frozenset({"tonapi"}),
        supported_explorers=frozenset({"tonviewer"}),
        excluded_tools=frozenset(
            {
                "gasless_transfer",
                "resolve_domain",
                "get_dns_records",
                "set_dns_wallet_record",
                "delete_dns_wallet_record",
            }
        ),
    ),
}
"""Per-network capabilities: supported providers, explorers, and excluded tools."""

CACHE_TTL_RESOLVE_DESTINATION: t.Final[int] = 30
"""Resolve .ton/.t.me domain to wallet address."""

CACHE_TTL_WALLET_ADDRESS: t.Final[int] = 0
"""Jetton wallet address for owner — immutable on-chain."""

CACHE_TTL_PUBLIC_KEY: t.Final[int] = 0
"""Wallet public key — immutable on-chain."""

CACHE_TTL_JETTON_METADATA: t.Final[int] = 300
"""Jetton metadata (name, symbol, decimals)."""

CACHE_TTL_ROYALTY_PARAMS: t.Final[int] = 300
"""Collection royalty params."""
