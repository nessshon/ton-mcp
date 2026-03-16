from __future__ import annotations

import typing as t

from pytoniq_core import Address
from tonutils.contracts.base import BaseContract
from tonutils.types import DNSCategory
from tonutils.utils import to_amount

from ton_mcp.models import ContractInfoResult
from ton_mcp.constants import CACHE_TTL_RESOLVE_DESTINATION
from ton_mcp.utils.cache import async_ttl_cache

if t.TYPE_CHECKING:
    from ton_mcp.core.context import AppContext


def safe_address(addr: t.Any, is_bounceable: bool = False) -> t.Optional[str]:
    """Convert address to string, or None if not a valid Address.

    Handles None, Slice (addr_none), and other non-Address types gracefully.

    :param addr: Address object, Slice, or None.
    :param is_bounceable: Whether to use bounceable format.
    :return: Address string or None.
    """
    if addr is None:
        return None
    try:
        return addr.to_str(is_bounceable=is_bounceable)
    except (Exception,):
        return None


@async_ttl_cache(CACHE_TTL_RESOLVE_DESTINATION)
async def resolve_destination(ctx: AppContext, destination: str) -> str:
    """Resolve destination address.

    If ``destination`` is a ``.ton`` or ``.t.me`` domain, resolves it
    to a wallet address via TON DNS.  Otherwise, returns as-is.

    :param ctx: Application context.
    :param destination: TON address or DNS domain.
    :return: Non-bounceable TON address string.
    :raises ValueError: If domain has no linked wallet record.
    """
    if not any(destination.endswith(suffix) for suffix in (".ton", ".t.me")):
        return destination

    record = await ctx.client.dnsresolve(
        domain=destination,
        category=DNSCategory.WALLET,
    )
    if record is None:
        raise ValueError(f"Domain '{destination}' has no wallet record.")

    return record.value.to_str(is_bounceable=False)


async def fetch_contract_info(ctx: AppContext, address: str) -> ContractInfoResult:
    """Fetch on-chain contract information.

    :param ctx: Application context.
    :param address: TON address to query.
    :return: Contract info result.
    """
    contract = await BaseContract.from_address(ctx.client, Address(address))

    return ContractInfoResult(
        address=contract.address.to_str(is_bounceable=False),
        balance=f"{to_amount(contract.balance, precision=4)} TON",
        balance_nano=contract.balance,
        state=contract.state.value,
        last_transaction_lt=contract.last_transaction_lt or None,
        last_transaction_hash=contract.last_transaction_hash or None,
    )
