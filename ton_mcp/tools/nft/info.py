from __future__ import annotations

import typing as t

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import CollectionInfoResult, NFTInfoResult
from ton_mcp.utils import safe_address
from ton_mcp.utils.getters import (
    get_authority_address,
    get_collection_data,
    get_nft_data,
    get_revoked_time,
    royalty_params,
)
from ton_mcp.utils.content import (
    parse_collection_content,
    parse_metadata,
    resolve_items_prefix_uri,
    resolve_nft_item_content,
)


async def get_collection_info(
    collection_address: str,
    app_ctx: AppContext = APP_CTX,
) -> CollectionInfoResult:
    """Get NFT collection metadata, owner, item count, and royalty info."""
    client = app_ctx.client

    data = await get_collection_data(
        client=client,
        address=collection_address,
    )

    next_item_index = int(data[0])
    owner_str = safe_address(data[2])
    content_cell = data[1]

    metadata: t.Optional[t.Dict[str, t.Any]] = None
    content_uri: t.Optional[str] = None
    hint: t.Optional[str] = None
    name: t.Optional[str] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None

    if content_cell is not None:
        try:
            metadata, content_uri, hint = await parse_collection_content(
                content_cell,
            )
        except (Exception,):
            hint = "Failed to parse collection metadata"

    if metadata:
        name = metadata.get("name")
        description = metadata.get("description")
        image = metadata.get("image")

    items_prefix_uri: t.Optional[str] = None
    if next_item_index > 0:
        items_prefix_uri = await resolve_items_prefix_uri(
            client=client,
            collection_address=collection_address,
        )

    royalty_percent: t.Optional[float] = None
    royalty_addr: t.Optional[str] = None

    try:
        royalty = await royalty_params(
            client=client,
            address=collection_address,
        )
        numerator = int(royalty[0])
        denominator = int(royalty[1])
        if denominator > 0:
            royalty_percent = round(numerator / denominator * 100, 2)
        royalty_addr = safe_address(royalty[2])
    except (Exception,):
        pass

    return CollectionInfoResult(
        address=collection_address,
        next_item_index=next_item_index,
        owner=owner_str,
        name=name,
        description=description,
        image=image,
        content_uri=content_uri,
        items_prefix_uri=items_prefix_uri,
        royalty_percent=royalty_percent,
        royalty_address=royalty_addr,
        metadata=metadata,
        hint=hint,
    )


async def get_nft_info(
    nft_address: str,
    app_ctx: AppContext = APP_CTX,
) -> NFTInfoResult:
    """Get NFT item metadata, owner, and collection info.

    For SBT items, also returns ``authority_address`` and ``revoked_at``.
    """
    client = app_ctx.client

    data = await get_nft_data(
        client=client,
        address=nft_address,
    )

    initialized = bool(data[0])
    index = int(data[1])
    collection_addr = safe_address(data[2])
    owner_str = safe_address(data[3])
    individual_content = data[4]

    metadata: t.Optional[t.Dict[str, t.Any]] = None
    hint: t.Optional[str] = None
    name: t.Optional[str] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None

    if initialized and individual_content is not None:
        try:
            if collection_addr is not None:
                metadata, hint = await resolve_nft_item_content(
                    client=client,
                    collection_address=collection_addr,
                    index=index,
                    individual_content=individual_content,
                )
            else:
                metadata, hint = await parse_metadata(individual_content)
        except (Exception,):
            hint = "Failed to parse NFT item metadata"

    if metadata:
        name = metadata.get("name")
        description = metadata.get("description")
        image = metadata.get("image")

    authority_addr: t.Optional[str] = None
    revoked_at: t.Optional[int] = None
    if initialized:
        try:
            authority = await get_authority_address(
                client=client,
                address=nft_address,
            )
            if authority is not None:
                authority_addr = authority.to_str(
                    is_bounceable=False,
                )
            revoked_at = await get_revoked_time(
                client=client,
                address=nft_address,
            )
        except (Exception,):
            pass

    return NFTInfoResult(
        address=nft_address,
        initialized=initialized,
        index=index,
        collection=collection_addr,
        owner=owner_str,
        name=name,
        description=description,
        image=image,
        authority_address=authority_addr,
        revoked_at=revoked_at,
        metadata=metadata,
        hint=hint,
    )
