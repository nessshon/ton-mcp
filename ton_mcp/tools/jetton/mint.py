from __future__ import annotations

from tonutils.contracts import (
    JettonInternalTransferBody,
    JettonMintBody,
)
from tonutils.utils import to_nano

from ton_mcp.constants import (
    FORWARD_MINT_JETTON,
    FORWARD_NOTIFY,
    GAS_MINT_JETTON,
)
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import TransactionResult
from ton_mcp.core.sender import format_send_result


async def mint_jetton(
    jetton_master_address: str,
    destination: str,
    amount: str,
    decimals: int = 9,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Mint jettons to an address. Irreversible.

    Admin-only. If caller is not admin, tx executes but is silently
    rejected on-chain. Wrong decimals silently mints wrong amount —
    call ``get_jetton_info`` to verify first.
    """
    jetton_amount = to_nano(amount, decimals=decimals)

    internal_transfer = JettonInternalTransferBody(
        jetton_amount=jetton_amount,
        response_address=destination,
        forward_amount=FORWARD_NOTIFY,
    )

    body = JettonMintBody(
        internal_transfer=internal_transfer,
        destination=destination,
        forward_amount=FORWARD_MINT_JETTON,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_master_address,
                amount=GAS_MINT_JETTON,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Jetton mint", 1, result)
