from __future__ import annotations

import asyncio
import typing as t

from tonutils.clients.protocol import ClientProtocol
from tonutils.exceptions import RunGetMethodError
from tonutils.utils import to_amount

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import JettonBalanceResult, JettonInfoResult
from ton_mcp.utils import safe_address
from ton_mcp.constants import CACHE_TTL_JETTON_METADATA
from ton_mcp.utils.cache import async_ttl_cache
from ton_mcp.utils.content import parse_metadata
from ton_mcp.utils.getters import get_jetton_data, get_wallet_address, get_wallet_data


async def get_jetton_info(
    jetton_master_address: str,
    app_ctx: AppContext = APP_CTX,
) -> JettonInfoResult:
    """Get token metadata, supply, and admin info.

    Returns ``decimals`` needed for all jetton operations.
    """
    data = await get_jetton_data(
        client=app_ctx.client,
        address=jetton_master_address,
    )

    total_supply = int(data[0])
    admin_str = safe_address(data[2])

    decimals, symbol, hint = await fetch_jetton_metadata(
        app_ctx.client,
        jetton_master_address,
    )

    metadata: t.Optional[t.Dict[str, t.Any]] = None
    name: t.Optional[str] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None

    content_cell = data[3]
    if content_cell is not None:
        try:
            metadata, meta_hint = await parse_metadata(content_cell)
            if hint is None:
                hint = meta_hint
        except (Exception,):
            if hint is None:
                hint = "Failed to parse jetton metadata"

    if metadata:
        name = metadata.get("name")
        description = metadata.get("description")
        image = metadata.get("image")

    total_supply_formatted: t.Optional[str] = None
    if decimals is not None:
        total_supply_formatted = str(
            to_amount(total_supply, decimals=decimals),
        )

    return JettonInfoResult(
        address=jetton_master_address,
        total_supply=total_supply,
        total_supply_formatted=total_supply_formatted,
        mintable=bool(data[1]),
        admin=admin_str,
        name=name,
        symbol=symbol or (metadata.get("symbol") if metadata else None),
        decimals=decimals,
        description=description,
        image=image,
        metadata=metadata,
        hint=hint,
    )


async def get_jetton_balance(
    jetton_master_address: str,
    owner_address: t.Optional[str] = None,
    app_ctx: AppContext = APP_CTX,
) -> JettonBalanceResult:
    """Get jetton balance for a wallet.

    If owner not specified, uses connected wallet.
    """
    if owner_address is None:
        owner_address = await app_ctx.sender.get_address()

    jetton_wallet_address = await get_wallet_address(
        client=app_ctx.client,
        address=jetton_master_address,
        owner_address=owner_address,
    )

    balance_coro = _fetch_wallet_balance(app_ctx.client, jetton_wallet_address)
    metadata_coro = fetch_jetton_metadata(app_ctx.client, jetton_master_address)
    (balance, wallet_str), (decimals, symbol, hint) = await asyncio.gather(
        balance_coro,
        metadata_coro,
    )

    balance_formatted: t.Optional[str] = None
    if decimals is not None:
        balance_formatted = str(to_amount(balance, decimals=decimals))

    return JettonBalanceResult(
        owner=owner_address,
        jetton_wallet=wallet_str,
        balance=balance,
        balance_formatted=balance_formatted,
        decimals=decimals,
        symbol=symbol,
        hint=hint,
    )


async def _fetch_wallet_balance(
    client: ClientProtocol,
    jetton_wallet_address: t.Any,
) -> t.Tuple[int, t.Optional[str]]:
    """Fetch jetton wallet balance.

    :param client: TON client instance.
    :param jetton_wallet_address: Jetton wallet contract address.
    :return: Tuple of (balance in base units, wallet address string or None).
    """
    try:
        data = await get_wallet_data(
            client=client,
            address=jetton_wallet_address,
        )
        return int(data[0]), jetton_wallet_address.to_str(is_bounceable=False)
    except RunGetMethodError:
        return 0, None


@async_ttl_cache(CACHE_TTL_JETTON_METADATA)
async def fetch_jetton_metadata(
    client: ClientProtocol,
    jetton_master_address: str,
) -> t.Tuple[t.Optional[int], t.Optional[str], t.Optional[str]]:
    """Fetch decimals and symbol from jetton master metadata.

    :param client: TON client instance.
    :param jetton_master_address: Jetton master contract address.
    :return: Tuple of (decimals, symbol, hint).
    """
    try:
        data = await get_jetton_data(
            client=client,
            address=jetton_master_address,
        )
        content_cell = data[3]
        if content_cell is None:
            return None, None, None

        metadata, hint = await parse_metadata(content_cell)
        decimals: t.Optional[int] = None
        raw_decimals = metadata.get("decimals")
        if raw_decimals is not None:
            try:
                decimals = int(raw_decimals)
            except (ValueError, TypeError):
                pass

        return decimals, metadata.get("symbol"), hint
    except (Exception,):
        return None, None, None
