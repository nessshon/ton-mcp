from __future__ import annotations

import typing as t

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import (
    JettonTransfer,
    NFTTransfer,
    TonTransfer,
    TransactionResult,
)
from ton_mcp.constants import FORWARD_NOTIFY, GAS_TRANSFER
from ton_mcp.core.sender import format_send_result
from ton_mcp.utils import resolve_destination, serialize_comment
from ton_mcp.utils.getters import get_wallet_address
from tonutils.contracts import (
    JettonTransferBody,
    NFTTransferBody,
)
from tonutils.utils import to_nano


async def batch_send_ton(
    transfers: t.List[TonTransfer],
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send TON to multiple addresses in a single transaction. Irreversible."""
    messages = []
    for tr in transfers:
        resolved = await resolve_destination(app_ctx, tr.destination)
        body = tr.comment if tr.comment else None
        messages.append(
            SendMessage(destination=resolved, amount=to_nano(tr.amount), body=body)
        )
    result = await app_ctx.sender.send(messages)
    return format_send_result("TON transfer", len(messages), result)


async def batch_send_jetton(
    transfers: t.List[JettonTransfer],
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Send jettons to multiple addresses in a single transaction. Irreversible.

    Each transfer can target a different jetton with its own decimals.
    Wrong decimals silently sends the wrong amount —
    call ``get_jetton_info`` to verify first.
    """
    my_address = await app_ctx.sender.get_address()
    messages = []

    for tr in transfers:
        resolved = await resolve_destination(app_ctx, tr.destination)
        jetton_wallet = await get_wallet_address(
            client=app_ctx.client,
            address=tr.jetton_master_address,
            owner_address=my_address,
        )
        jetton_amount = to_nano(tr.amount, decimals=tr.decimals)
        forward_payload = serialize_comment(tr.comment)
        body = JettonTransferBody(
            destination=resolved,
            jetton_amount=jetton_amount,
            response_address=my_address,
            forward_payload=forward_payload,
            forward_amount=FORWARD_NOTIFY,
        )
        messages.append(
            SendMessage(
                destination=jetton_wallet,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        )

    result = await app_ctx.sender.send(messages)
    return format_send_result("Jetton transfer", len(messages), result)


async def batch_send_nft(
    transfers: t.List[NFTTransfer],
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Transfer multiple NFTs in a single transaction. Irreversible."""
    my_address = await app_ctx.sender.get_address()
    messages = []

    for tr in transfers:
        resolved = await resolve_destination(app_ctx, tr.destination)
        forward_payload = serialize_comment(tr.comment)
        body = NFTTransferBody(
            destination=resolved,
            response_address=my_address,
            forward_payload=forward_payload,
            forward_amount=FORWARD_NOTIFY,
        )
        messages.append(
            SendMessage(
                destination=tr.nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        )

    result = await app_ctx.sender.send(messages)
    return format_send_result("NFT transfer", len(messages), result)
