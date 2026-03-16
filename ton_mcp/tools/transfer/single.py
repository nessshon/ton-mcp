from __future__ import annotations

import typing as t

from fastmcp.exceptions import ToolError
from pytoniq_core import Cell, StateInit
from tonutils.contracts import (
    JettonTransferBody,
    NFTTransferBody,
    WalletV5R1,
)
from tonutils.utils import TextCipher, to_cell, to_nano

from ton_mcp.constants import FORWARD_NOTIFY, GAS_TRANSFER
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.core.sender import format_send_result
from ton_mcp.models import (
    GaslessTransferResult,
    RawMessage,
    TransactionResult,
)
from ton_mcp.types import SendMessage
from ton_mcp.utils import resolve_destination, serialize_comment
from ton_mcp.utils.getters import get_public_key, get_wallet_address


async def send_ton(
    destination: str,
    amount: str,
    comment: str = "",
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send TON to an address. Irreversible.

    For multiple recipients, use ``batch_send_ton``.
    """
    resolved = await resolve_destination(app_ctx, destination)
    body = comment if comment else None

    result = await app_ctx.sender.send(
        [SendMessage(destination=resolved, amount=to_nano(amount), body=body)]
    )
    return format_send_result("TON transfer", 1, result)


async def send_jetton(
    destination: str,
    jetton_master_address: str,
    amount: str,
    decimals: int = 9,
    comment: str = "",
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send jettons to an address. Irreversible.

    For multiple recipients, use ``batch_send_jetton``.
    Wrong decimals silently sends the wrong amount —
    call ``get_jetton_info`` to verify first.
    """
    resolved = await resolve_destination(app_ctx, destination)
    my_address = await app_ctx.sender.get_address()

    jetton_wallet = await get_wallet_address(
        client=app_ctx.client,
        address=jetton_master_address,
        owner_address=my_address,
    )

    jetton_amount = to_nano(amount, decimals=decimals)
    forward_payload = serialize_comment(comment)
    body = JettonTransferBody(
        destination=resolved,
        jetton_amount=jetton_amount,
        response_address=my_address,
        forward_payload=forward_payload,
        forward_amount=FORWARD_NOTIFY,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_wallet,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ]
    )
    return format_send_result("Jetton transfer", 1, result)


async def send_nft(
    destination: str,
    nft_address: str,
    comment: str = "",
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Transfer an NFT to another address. Irreversible.

    For multiple NFTs, use ``batch_send_nft``.
    """
    resolved = await resolve_destination(app_ctx, destination)
    my_address = await app_ctx.sender.get_address()

    forward_payload = serialize_comment(comment)
    body = NFTTransferBody(
        destination=resolved,
        response_address=my_address,
        forward_payload=forward_payload,
        forward_amount=FORWARD_NOTIFY,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ]
    )
    return format_send_result("NFT transfer", 1, result)


async def send_encrypted(
    destination: str,
    amount: str,
    message: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send TON with an encrypted text message. Irreversible.

    SECRET_KEY mode only. Recipient wallet must be deployed.
    """
    if app_ctx.wallet is None or app_ctx.wallet.private_key is None:
        raise ToolError(
            "WALLET_SECRET: Encrypted messages require "
            "SECRET_KEY mode with a private key."
        )

    resolved = await resolve_destination(app_ctx, destination)

    their_public_key = await get_public_key(
        client=app_ctx.client,
        address=resolved,
    )

    body = TextCipher.encrypt(
        payload=message,
        sender_address=app_ctx.wallet.address,
        our_private_key=app_ctx.wallet.private_key,
        their_public_key=their_public_key,
    )

    result = await app_ctx.sender.send(
        [SendMessage(destination=resolved, amount=to_nano(amount), body=body)]
    )
    return format_send_result("Encrypted transfer", 1, result)


async def gasless_transfer(
    destination: str,
    jetton_master_address: str,
    amount: str,
    decimals: int = 9,
    app_ctx: AppContext = APP_CTX,
) -> GaslessTransferResult:
    """Send jettons without paying TON for gas. Irreversible.

    Commission is deducted from the jetton balance instead of TON.
    Requires SECRET_KEY mode with WalletV5R1, tonapi provider, mainnet only.
    Jetton must be supported by the relay (e.g. USDT).
    """
    if app_ctx.wallet is None:
        raise ToolError("WALLET_SECRET: Gasless transfers require SECRET_KEY mode.")

    if not isinstance(app_ctx.wallet, WalletV5R1):
        raise ToolError("WALLET_VERSION: Gasless transfers require WalletV5R1.")

    resolved = await resolve_destination(app_ctx, destination)
    jetton_amount = to_nano(amount, decimals=decimals)

    estimate = await app_ctx.wallet.gasless_estimate(
        destination=resolved,
        jetton_amount=jetton_amount,
        jetton_master_address=jetton_master_address,
    )

    await app_ctx.wallet.gasless_send(estimate)

    return GaslessTransferResult(
        commission=estimate.commission,
    )


async def send_raw(
    messages: t.List[RawMessage],
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send raw messages with custom body and state_init. Irreversible.

    Amounts are in nanotons. Body and state_init accept hex or base64.
    """
    internal = []

    for msg in messages:
        state_init = None
        if msg.state_init is not None:
            state_init = StateInit.deserialize(to_cell(msg.state_init).begin_parse())
        body: t.Optional[t.Union[str, Cell]] = msg.body
        if body is not None:
            try:
                body = to_cell(body)
            except (Exception,):
                pass
        internal.append(
            SendMessage(
                destination=msg.destination,
                amount=int(msg.amount),
                body=body,
                state_init=state_init,
            )
        )

    result = await app_ctx.sender.send(internal)
    return format_send_result("Raw transaction", len(internal), result)
