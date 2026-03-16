from __future__ import annotations

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import TransactionResult
from ton_mcp.core.sender import format_send_result
from tonutils.contracts import (
    ChangeDNSRecordBody,
    DNSRecordWallet,
)
from tonutils.types import DNSCategory

from ton_mcp.constants import GAS_TRANSFER


async def set_dns_wallet_record(
    dns_item_address: str,
    wallet_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Link a wallet address to a .ton/.t.me domain. Irreversible.

    Domain owner only. Requires NFT contract address, not domain name.
    """
    body = ChangeDNSRecordBody(
        category=DNSCategory.WALLET,
        record=DNSRecordWallet(wallet_address),
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=dns_item_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("DNS wallet record set", 1, result)


async def delete_dns_wallet_record(
    dns_item_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Remove wallet link from a .ton/.t.me domain. Irreversible.

    Domain owner only. Requires NFT contract address, not domain name.
    """
    body = ChangeDNSRecordBody(
        category=DNSCategory.WALLET,
        record=None,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=dns_item_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("DNS wallet record deleted", 1, result)
