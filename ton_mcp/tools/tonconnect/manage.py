from __future__ import annotations

import typing as t

from fastmcp.exceptions import ToolError
from tonutils.tonconnect import Connector
from tonutils.tonconnect.models import TonProofPayloadDto, Wallet
from tonutils.tonconnect.utils.signing import (
    VerifyTonProof,
    create_ton_proof_payload,
    verify_ton_proof_payload,
)

from ton_mcp.constants import TONCONNECT_SESSION_KEY
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import ConnectWalletResult, WalletInfoResult
from ton_mcp.utils import make_qr_url, shorten_urls


async def connect_wallet(
    app_ctx: AppContext = APP_CTX,
) -> t.Union[ConnectWalletResult, WalletInfoResult]:
    """Start or restore a TonConnect wallet connection.

    If existing session found, returns wallet info immediately.
    Otherwise, returns QR code and wallet deep links — show all links
    to the user, then immediately call ``await_wallet_connection``.
    """
    tc = app_ctx.tc

    connector = tc.create_connector(TONCONNECT_SESSION_KEY)
    if await connector.restore():
        return _build_wallet_info(connector)

    ton_proof_payload = create_ton_proof_payload(
        secret_key=app_ctx.config.tonconnect_secret,
    )
    request = connector.make_connect_request(
        ton_proof_payload=ton_proof_payload,
    )
    universal_url = await connector.connect(
        request=request,
        network=app_ctx.config.network,
    )

    urls_to_shorten = [make_qr_url(universal_url)]
    wallet_names = []
    for app_wallet in tc.app_wallets:
        urls_to_shorten.append(connector.make_connect_url(request, app_wallet))
        wallet_names.append(app_wallet.name)

    shortened = await shorten_urls(urls_to_shorten)

    qr_url = shortened[0]
    wallets = dict(zip(wallet_names, shortened[1:]))

    return ConnectWalletResult(
        qr_code_link=qr_url,
        wallets=wallets,
        hint=(
            f"Show QR code link (opens scannable QR, "
            f"supports: {', '.join(wallet_names)}). "
            f"Then list each wallet as: WalletName: link. "
            f"Always show the wallet name before its link."
        ),
    )


async def await_wallet_connection(
    app_ctx: AppContext = APP_CTX,
) -> WalletInfoResult:
    """Wait for wallet to connect after ``connect_wallet``.

    Blocks until the user approves in their wallet app.
    """
    connector = app_ctx.tc.connectors.get(TONCONNECT_SESSION_KEY)
    if connector is None:
        raise ToolError("No pending connection. Call connect_wallet first.")

    if connector.connected:
        wallet = connector.wallet
    else:
        wallet, error = await connector.wait_connect()
        if error is not None:
            raise ToolError(f"Connection failed: {error}")

    if wallet is not None:
        await _verify_ton_proof(app_ctx, connector, wallet)

    return _build_wallet_info(connector)


async def disconnect_wallet(
    app_ctx: AppContext = APP_CTX,
) -> WalletInfoResult:
    """Disconnect the TonConnect wallet."""
    connector = app_ctx.tc.connectors.get(TONCONNECT_SESSION_KEY)
    if connector is None:
        connector = app_ctx.tc.create_connector(TONCONNECT_SESSION_KEY)
        if not await connector.restore():
            raise ToolError("No wallet connected.")

    if not connector.connected:
        raise ToolError("No wallet connected.")

    info = _build_wallet_info(connector)
    await connector.disconnect()

    return info


async def _verify_ton_proof(
    app_ctx: AppContext,
    connector: Connector,
    wallet: Wallet,
) -> None:
    """Verify TonProof challenge from connected wallet.

    :param app_ctx: Application context.
    :param connector: Active TonConnect connector.
    :param wallet: Wallet connection result with proof data.
    :raises ToolError: If TonProof verification fails.
    """
    if wallet.ton_proof is None:
        return

    try:
        verify_ton_proof_payload(
            secret_key=app_ctx.config.tonconnect_secret,
            ton_proof_payload=wallet.ton_proof.payload,
        )
        proof_dto = TonProofPayloadDto(
            address=wallet.account.address,
            network=wallet.account.network,
            public_key=wallet.account.public_key,
            wallet_state_init=wallet.account.state_init,
            proof=wallet.ton_proof,
        )
        await VerifyTonProof(proof_dto).verify(
            allowed_domains=app_ctx.config.tonconnect_app_domains,
        )
    except Exception as e:
        await connector.disconnect()
        raise ToolError(f"TonProof verification failed: {e}") from e


def _build_wallet_info(connector: Connector) -> WalletInfoResult:
    """Build wallet info result from connector.

    :param connector: Active TonConnect connector.
    :return: Wallet info model.
    """
    return WalletInfoResult(
        wallet=connector.app_wallet.name if connector.app_wallet else "Unknown",
        address=connector.account.address.to_str(is_bounceable=False),
        network=connector.account.network.name,
    )
