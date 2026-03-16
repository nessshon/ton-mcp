from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core import Address, MessageAny, Transaction
from tonutils.types import NetworkGlobalID
from tonutils.utils import normalize_hash

from ton_mcp.types import SendResult
from ton_mcp.utils.urls import explorer_url

if t.TYPE_CHECKING:
    from fastmcp import Context
    from tonutils.clients.protocol import ClientProtocol


async def confirm_transaction(
    client: ClientProtocol,
    address: Address,
    normalized_hash: str,
    network: NetworkGlobalID,
    explorer: str,
    ctx: t.Optional[Context] = None,
    last_transaction_lt: t.Optional[int] = None,
    last_transaction_hash: t.Optional[str] = None,
    timeout: int = 30,
) -> SendResult:
    """Poll blockchain until transaction confirmed.

    :param client: Blockchain client.
    :param address: Wallet address to monitor.
    :param normalized_hash: Expected transaction hash.
    :param network: Network name for explorer URL.
    :param explorer: Explorer name for URL generation.
    :param ctx: Optional FastMCP context for progress reporting.
    :param last_transaction_lt: Last known transaction logical time.
    :param last_transaction_hash: Last known transaction hash.
    :param timeout: Maximum seconds to wait for confirmation.
    :return: Confirmed send result with hash and explorer URL.
    :raises ValueError: If transaction not confirmed within timeout.
    """
    poll_interval: float = 0.5
    elapsed: float = 0

    while elapsed < timeout:
        _report_progress(
            ctx, elapsed, timeout, f"Waiting for confirmation... ({elapsed}s)"
        )

        if not await _account_unchanged(
            client, address, last_transaction_lt, last_transaction_hash
        ) and _find_in_transactions(
            await client.get_transactions(address=address, limit=100),
            normalized_hash,
            last_transaction_lt,
            last_transaction_hash,
        ):
            _report_progress(ctx, timeout, timeout, "Confirmed!")
            return SendResult(
                normalized_hash=normalized_hash,
                explorer_url=explorer_url(network, normalized_hash, explorer),
            )

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    url = explorer_url(network, normalized_hash, explorer)
    raise ValueError(
        f"Transaction not confirmed within {timeout}s. "
        f"This does NOT mean it failed — it may still be processing. "
        f"Check the explorer: {url}"
    )


def _report_progress(
    ctx: t.Optional[Context],
    current: float,
    total: float,
    message: str,
) -> None:
    """Schedule progress report if context is available."""
    if ctx is not None:
        asyncio.ensure_future(ctx.report_progress(current, total, message))


async def _account_unchanged(
    client: ClientProtocol,
    address: Address,
    last_lt: t.Optional[int],
    last_hash: t.Optional[str],
) -> bool:
    """Check if account state has not changed since last known transaction."""
    if last_lt is None or last_hash is None:
        return False

    info = await client.get_info(address)
    return (
        info.last_transaction_lt == last_lt and info.last_transaction_hash == last_hash
    )


def _find_in_transactions(
    transactions: t.List[Transaction],
    normalized_hash: str,
    last_lt: t.Optional[int],
    last_hash: t.Optional[str],
) -> bool:
    """Search transactions for a message matching the normalized hash."""
    for tx in transactions:
        if last_lt is not None and last_hash is not None:
            if tx.lt == last_lt and tx.cell.hash.hex() == last_hash:
                continue
        msgs: t.List[MessageAny] = []
        if tx.in_msg is not None:
            msgs.append(tx.in_msg)
        if tx.out_msgs is not None:
            msgs.extend(tx.out_msgs)
        if any(normalize_hash(msg) == normalized_hash for msg in msgs):
            return True
    return False
