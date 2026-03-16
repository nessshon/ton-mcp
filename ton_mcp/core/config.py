from __future__ import annotations

import os
import socket
import typing as t

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tonutils.types import NetworkGlobalID

from ton_mcp.constants import NETWORK_CAPABILITIES
from ton_mcp.types import SignMethod


class Config(BaseSettings):
    """TON MCP server configuration.

    All values are read from environment variables or a `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
    )

    network: NetworkGlobalID = NetworkGlobalID.TESTNET
    """Network: ``mainnet``, ``testnet``, or ``tetra``."""

    explorer: str = "tonviewer"
    """Transaction explorer: ``tonviewer`` or ``tonscan``."""

    wallet_version: str = "v5r1"
    """Wallet version: ``v3r1``, ``v3r2``, ``v4r1``, ``v4r2``, ``v5r1``, ``highload_v3r1``, ``preprocessed_v2``."""

    wallet_secret: t.Optional[str] = None
    """Mnemonic (12/18/24 words) or private key (hex/base64). If empty, TonConnect mode is used."""

    client_provider: t.Optional[str] = None
    """Client provider: ``toncenter``, ``tonapi``, or ``lite``."""

    client_api_key: t.Optional[str] = None
    """API key. Required for ``tonapi``, optional for ``toncenter``."""

    client_lite_config: t.Optional[str] = None
    """Lite client config: file path or URL. If empty, uses public network config."""

    client_rps_limit: int = 10
    """Requests per second limit."""

    client_rps_period: float = 1.0
    """Rate limit time window in seconds."""

    tonconnect_manifest_url: str = (
        "https://raw.githubusercontent.com/nessshon/ton-mcp/main/"
        "assets/tonconnect-manifest.json"
    )
    """TonConnect manifest URL."""

    tonconnect_storage_path: str = "./tonconnect-storage.json"
    """Path to TonConnect session storage file."""

    tonconnect_app_domains: t.List[str] = ["github.com"]
    """Allowed domains for TonProof verification."""

    tonconnect_secret: str = "ton-mcp-secret"
    """Secret for TonProof HMAC signing."""

    mcp_server_host: str = "127.0.0.1"
    """MCP server host."""

    mcp_server_port: int = 0
    """MCP server port. 0 = auto-select free port."""

    @property
    def sign_method(self) -> SignMethod:
        """Determine signing method based on configuration."""
        if self.wallet_secret:
            return SignMethod.SECRET_KEY
        return SignMethod.TONCONNECT

    @property
    def is_mnemonic(self) -> bool:
        """Check if secret key is a mnemonic phrase."""
        return bool(self.wallet_secret and " " in self.wallet_secret)

    @staticmethod
    def _parse_network_str(value: str) -> NetworkGlobalID:
        """Convert string network name to NetworkGlobalID.

        :param value: Network name string.
        :return: NetworkGlobalID enum value.
        :raises ValueError: If network name is unknown.
        """
        networks = {
            "mainnet": NetworkGlobalID.MAINNET,
            "testnet": NetworkGlobalID.TESTNET,
            "tetra": NetworkGlobalID.TETRA,
        }
        result = networks.get(value.lower())
        if result is None:
            raise ValueError(
                f"Unknown network: {value}. "
                f"Use: {', '.join(sorted(networks.keys()))}."
            )
        return result

    @field_validator("network", mode="before")
    @classmethod
    def _parse_network(cls, v: t.Any) -> NetworkGlobalID:
        """Convert string network name to NetworkGlobalID."""
        if isinstance(v, NetworkGlobalID):
            return v
        if isinstance(v, str):
            return cls._parse_network_str(v)
        raise ValueError(f"Unknown network: {v}.")

    @model_validator(mode="after")
    def _resolve_server_port(self) -> Config:
        """Auto-select a free port when ``mcp_server_port`` is 0."""
        if self.mcp_server_port == 0:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.mcp_server_host, 0))
                self.mcp_server_port = s.getsockname()[1]
        return self

    @model_validator(mode="after")
    def _validate_network_support(self) -> Config:
        """Validate provider and explorer are supported on configured network."""
        caps = NETWORK_CAPABILITIES.get(self.network)
        if caps is None:
            raise ValueError(
                f"No capabilities defined for network {self.network.name}. "
                f"Add entry to NETWORK_CAPABILITIES."
            )
        if (
            self.client_provider
            and self.client_provider not in caps.supported_providers
        ):
            raise ValueError(
                f"Provider '{self.client_provider}' not supported on {self.network.name}. "
                f"Use: {', '.join(sorted(caps.supported_providers))}."
            )
        if self.explorer not in caps.supported_explorers:
            raise ValueError(
                f"Explorer '{self.explorer}' not supported on {self.network.name}. "
                f"Use: {', '.join(sorted(caps.supported_explorers))}."
            )
        return self


config = Config()
