from __future__ import annotations

from ton_mcp.constants import INCLUDE_WALLETS, WALLET_VERSIONS
from ton_mcp.core.config import Config
from ton_mcp.core.context import AppContext
from ton_mcp.core.sender import Sender
from tonutils.clients import (
    LiteBalancer,
    TonapiClient,
    ToncenterClient,
)
from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.storage import FileStorage
from tonutils.tonconnect.utils import AppWalletsLoader
from tonutils.types import (
    DEFAULT_HTTP_RETRY_POLICY,
    DEFAULT_ADNL_RETRY_POLICY,
)
from tonutils.types import PrivateKey


def create_client(config: Config) -> ClientProtocol:
    """Create a blockchain client based on configuration.

    :param config: Server configuration.
    :return: Client instance (not yet connected).
    :raises ValueError: If provider is unknown or required params are missing.
    """
    network = config.network

    if not config.client_provider:
        raise ValueError(
            "CLIENT_PROVIDER: Client provider is required."
            " Use 'toncenter', 'tonapi', or 'lite'."
        )

    if config.client_provider == "toncenter":
        return ToncenterClient(
            network=network,
            api_key=config.client_api_key,
            rps_limit=config.client_rps_limit,
            rps_period=config.client_rps_period,
            retry_policy=DEFAULT_HTTP_RETRY_POLICY,
        )

    if config.client_provider == "tonapi":
        if not config.client_api_key:
            raise ValueError(
                "CLIENT_API_KEY: API key is required"
                " for tonapi provider."
            )
        return TonapiClient(
            network=network,
            api_key=config.client_api_key,
            rps_limit=config.client_rps_limit,
            rps_period=config.client_rps_period,
            retry_policy=DEFAULT_HTTP_RETRY_POLICY,
        )

    if config.client_provider == "lite":
        if config.client_lite_config:
            return LiteBalancer.from_config(
                network=network,
                config=config.client_lite_config,
                rps_limit=config.client_rps_limit,
                retry_policy=DEFAULT_ADNL_RETRY_POLICY,
            )
        return LiteBalancer.from_network_config(
            network=network,
            rps_limit=config.client_rps_limit,
            retry_policy=DEFAULT_ADNL_RETRY_POLICY,
        )

    raise ValueError(
        f"CLIENT_PROVIDER: Unknown provider:"
        f" {config.client_provider}."
        " Use 'toncenter', 'tonapi', or 'lite'."
    )


def restore_wallet(client: ClientProtocol, config: Config) -> BaseWallet:
    """Restore a wallet instance from secret key.

    :param client: Connected blockchain client.
    :param config: Server configuration.
    :return: Wallet instance.
    :raises ValueError: If wallet version is unknown.
    """
    wallet_cls = WALLET_VERSIONS.get(config.wallet_version)
    if wallet_cls is None:
        raise ValueError(
            f"WALLET_VERSION: Unknown version: {config.wallet_version}. "
            f"Available: {', '.join(WALLET_VERSIONS.keys())}."
        )

    try:
        if config.is_mnemonic:
            wallet, _, _, _ = wallet_cls.from_mnemonic(client, config.wallet_secret)
        else:
            wallet = wallet_cls.from_private_key(
                client, PrivateKey(config.wallet_secret)
            )

    except Exception as e:
        raise ValueError(f"WALLET_SECRET: Invalid secret: {e}") from e

    return wallet


def create_tonconnect(config: Config) -> TonConnect:
    """Create TonConnect manager.

    :param config: Server configuration.
    :return: TonConnect instance.
    """
    loader = AppWalletsLoader(include_wallets=INCLUDE_WALLETS)
    storage = FileStorage(config.tonconnect_storage_path)
    app_wallets = loader.get_wallets()

    return TonConnect(
        storage=storage,
        manifest_url=config.tonconnect_manifest_url,
        app_wallets=app_wallets,
    )


def create_sender(app_ctx: AppContext) -> Sender:
    """Create Sender instance.

    :param app_ctx: Application context.
    :return: Sender instance.
    """
    return Sender(app_ctx)
