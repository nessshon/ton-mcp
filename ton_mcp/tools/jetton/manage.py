from __future__ import annotations

from tonutils.contracts import (
    JettonBurnBody,
    JettonChangeAdminBody,
    JettonChangeContentBody,
    JettonDropAdminBody,
    OffchainContent,
)
from tonutils.utils import to_nano

from ton_mcp.constants import GAS_TRANSFER
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import TransactionResult
from ton_mcp.core.sender import format_send_result
from ton_mcp.utils.getters import get_wallet_address


async def burn_jetton(
    jetton_master_address: str,
    amount: str,
    decimals: int = 9,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Burn jettons from your wallet. Irreversible.

    Wrong decimals silently burns wrong amount —
    call ``get_jetton_info`` to verify first.
    """
    my_address = await app_ctx.sender.get_address()

    jetton_wallet_address = await get_wallet_address(
        client=app_ctx.client,
        address=jetton_master_address,
        owner_address=my_address,
    )

    jetton_amount = to_nano(amount, decimals=decimals)

    body = JettonBurnBody(
        jetton_amount=jetton_amount,
        response_address=my_address,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_wallet_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Jetton burn", 1, result)


async def change_jetton_admin(
    jetton_master_address: str,
    new_admin_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Transfer jetton admin rights. Irreversible.

    Only current admin can transfer. New admin controls minting and metadata.
    """
    body = JettonChangeAdminBody(admin_address=new_admin_address)

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_master_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Admin change", 1, result)


async def change_jetton_content(
    jetton_master_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Update jetton metadata URI. Irreversible. Admin-only."""
    content = OffchainContent(uri=content_uri)
    body = JettonChangeContentBody(content=content)

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_master_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Content change", 1, result)


async def drop_jetton_admin(
    jetton_master_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Permanently remove admin from a jetton. IRREVERSIBLE.

    No one can mint or change metadata after this.
    """
    body = JettonDropAdminBody()

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_master_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Admin dropped", 1, result)
