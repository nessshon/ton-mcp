from __future__ import annotations

import typing as t

from tonutils.contracts import (
    get_authority_address_get_method as get_authority_address,
    get_collection_data_get_method as get_collection_data,
    get_jetton_data_get_method as get_jetton_data,
    get_nft_address_by_index_get_method as get_nft_address_by_index,
    get_nft_content_get_method as get_nft_content,
    get_nft_data_get_method as get_nft_data,
    get_public_key_get_method as _get_public_key,
    get_revoked_time_get_method as get_revoked_time,
    get_wallet_address_get_method as _get_wallet_address,
    get_wallet_data_get_method as get_wallet_data,
    royalty_params_get_method as _royalty_params,
)

from ton_mcp.constants import (
    CACHE_TTL_PUBLIC_KEY,
    CACHE_TTL_ROYALTY_PARAMS,
    CACHE_TTL_WALLET_ADDRESS,
)
from ton_mcp.utils.cache import async_ttl_cache

if t.TYPE_CHECKING:
    from tonutils.clients.protocol import ClientProtocol


@async_ttl_cache(CACHE_TTL_WALLET_ADDRESS)
async def get_wallet_address(
    client: ClientProtocol,
    address: str,
    owner_address: str,
) -> t.Any:
    """Jetton wallet address for owner. Immutable on-chain."""
    return await _get_wallet_address(
        client=client,
        address=address,
        owner_address=owner_address,
    )


@async_ttl_cache(CACHE_TTL_PUBLIC_KEY)
async def get_public_key(
    client: ClientProtocol,
    address: str,
) -> t.Any:
    """Wallet public key. Immutable on-chain."""
    return await _get_public_key(
        client=client,
        address=address,
    )


@async_ttl_cache(CACHE_TTL_ROYALTY_PARAMS)
async def royalty_params(
    client: ClientProtocol,
    address: str,
) -> t.Any:
    """Collection royalty params (numerator, denominator, address)."""
    return await _royalty_params(
        client=client,
        address=address,
    )


__all__ = [
    "get_authority_address",
    "get_collection_data",
    "get_jetton_data",
    "get_nft_address_by_index",
    "get_nft_content",
    "get_nft_data",
    "get_public_key",
    "get_revoked_time",
    "get_wallet_address",
    "get_wallet_data",
    "royalty_params",
]
