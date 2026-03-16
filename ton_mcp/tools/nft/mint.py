from __future__ import annotations

import asyncio
import typing as t

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pytoniq_core import Cell
from tonutils.contracts import (
    NFTCollectionBatchMintItemBody,
    NFTCollectionMintItemBody,
    NFTItemEditableMintRef,
    NFTItemSoulboundMintRef,
    NFTItemStandardMintRef,
    OffchainItemContent,
)
from ton_mcp.utils.getters import get_collection_data

from ton_mcp.constants import FORWARD_MINT_NFT, GAS_MINT_NFT
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import (
    BatchMintResult,
    EditableMintItem,
    MintItem,
    MintNFTResult,
    SoulboundMintItem,
)
from ton_mcp.types import SendMessage


async def mint_nft(
    collection_address: str,
    owner_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> MintNFTResult:
    """Mint a standard NFT item. Irreversible.

    Collection owner only. Index is auto-assigned.
    ``content_uri`` is a suffix (e.g. ``0.json``), not a full URL.
    """
    item_index = await _get_next_item_index(app_ctx, collection_address)

    ref = NFTItemStandardMintRef(
        owner_address=owner_address,
        content=OffchainItemContent(suffix_uri=content_uri),
    )

    body = NFTCollectionMintItemBody(
        item_index=item_index,
        item_ref=ref.serialize(),
        forward_amount=FORWARD_MINT_NFT,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection_address,
                amount=GAS_MINT_NFT,
                body=body.serialize(),
            )
        ],
    )

    return MintNFTResult(
        item_index=item_index,
        hash=result.normalized_hash,
        explorer=result.explorer_url,
    )


async def mint_soulbound_nft(
    collection_address: str,
    owner_address: str,
    authority_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> MintNFTResult:
    """Mint a soulbound NFT item (SBT). Irreversible.

    Collection owner only. Non-transferable after mint.
    Authority can revoke; owner can destroy.
    """
    item_index = await _get_next_item_index(app_ctx, collection_address)

    ref = NFTItemSoulboundMintRef(
        owner_address=owner_address,
        authority_address=authority_address,
        content=OffchainItemContent(suffix_uri=content_uri),
    )

    body = NFTCollectionMintItemBody(
        item_index=item_index,
        item_ref=ref.serialize(),
        forward_amount=FORWARD_MINT_NFT,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection_address,
                amount=GAS_MINT_NFT,
                body=body.serialize(),
            )
        ],
    )

    return MintNFTResult(
        item_index=item_index,
        hash=result.normalized_hash,
        explorer=result.explorer_url,
    )


async def mint_editable_nft(
    collection_address: str,
    owner_address: str,
    editor_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> MintNFTResult:
    """Mint an editable NFT item. Irreversible.

    Collection owner only. Editor can modify metadata after mint.
    """
    item_index = await _get_next_item_index(app_ctx, collection_address)

    ref = NFTItemEditableMintRef(
        owner_address=owner_address,
        editor_address=editor_address,
        content=OffchainItemContent(suffix_uri=content_uri),
    )

    body = NFTCollectionMintItemBody(
        item_index=item_index,
        item_ref=ref.serialize(),
        forward_amount=FORWARD_MINT_NFT,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection_address,
                amount=GAS_MINT_NFT,
                body=body.serialize(),
            )
        ],
    )

    return MintNFTResult(
        item_index=item_index,
        hash=result.normalized_hash,
        explorer=result.explorer_url,
    )


async def batch_mint_nft(
    collection_address: str,
    items: t.List[MintItem],
    ctx: Context,
    batch_size: int = 100,
    app_ctx: AppContext = APP_CTX,
) -> BatchMintResult:
    """Mint multiple standard NFT items. Irreversible.

    Collection owner only. Max 249 items per tx, default batch_size=100.
    Batches are sent sequentially with confirmation between each.
    """
    return await _batch_mint(
        app_ctx=app_ctx,
        ctx=ctx,
        collection_address=collection_address,
        items=items,
        batch_size=batch_size,
        build_ref=_build_standard_ref,
    )


async def batch_mint_soulbound_nft(
    collection_address: str,
    items: t.List[SoulboundMintItem],
    ctx: Context,
    batch_size: int = 100,
    app_ctx: AppContext = APP_CTX,
) -> BatchMintResult:
    """Mint multiple soulbound NFT items. Irreversible.

    Collection owner only. Max 249 per tx, default batch_size=100.
    """
    return await _batch_mint(
        app_ctx=app_ctx,
        ctx=ctx,
        collection_address=collection_address,
        items=items,
        batch_size=batch_size,
        build_ref=_build_soulbound_ref,
    )


async def batch_mint_editable_nft(
    collection_address: str,
    items: t.List[EditableMintItem],
    ctx: Context,
    batch_size: int = 100,
    app_ctx: AppContext = APP_CTX,
) -> BatchMintResult:
    """Mint multiple editable NFT items. Irreversible.

    Collection owner only. Max 249 per tx, default batch_size=100.
    """
    return await _batch_mint(
        app_ctx=app_ctx,
        ctx=ctx,
        collection_address=collection_address,
        items=items,
        batch_size=batch_size,
        build_ref=_build_editable_ref,
    )


async def _get_next_item_index(app_ctx: AppContext, collection_address: str) -> int:
    """Get the next item index from the collection contract.

    :param app_ctx: Application context.
    :param collection_address: NFT collection address.
    :return: Next item index for minting.
    """
    data = await get_collection_data(
        client=app_ctx.client,
        address=collection_address,
    )
    return int(data[0])


def _build_standard_ref(item: MintItem, _index: int) -> Cell:
    """Build standard NFT mint ref.

    :param item: Mint item data.
    :param _index: Item index.
    :return: Serialized mint ref.
    """
    return NFTItemStandardMintRef(
        owner_address=item.owner_address,
        content=OffchainItemContent(suffix_uri=item.content_uri),
    ).serialize()


def _build_soulbound_ref(item: SoulboundMintItem, _index: int) -> Cell:
    """Build soulbound NFT mint ref.

    :param item: Soulbound mint item data.
    :param _index: Item index.
    :return: Serialized mint ref.
    """
    return NFTItemSoulboundMintRef(
        owner_address=item.owner_address,
        authority_address=item.authority_address,
        content=OffchainItemContent(suffix_uri=item.content_uri),
    ).serialize()


def _build_editable_ref(item: EditableMintItem, _index: int) -> Cell:
    """Build editable NFT mint ref.

    :param item: Editable mint item data.
    :param _index: Item index.
    :return: Serialized mint ref.
    """
    return NFTItemEditableMintRef(
        owner_address=item.owner_address,
        editor_address=item.editor_address,
        content=OffchainItemContent(suffix_uri=item.content_uri),
    ).serialize()


async def _batch_mint(
    app_ctx: AppContext,
    ctx: Context,
    collection_address: str,
    items: t.Union[
        t.List[MintItem], t.List[SoulboundMintItem], t.List[EditableMintItem]
    ],
    batch_size: int,
    build_ref: t.Callable[..., Cell],
) -> BatchMintResult:
    """Mint NFT items in batches with confirmation between each.

    :param app_ctx: Application context.
    :param ctx: FastMCP context for progress reporting.
    :param collection_address: Collection address.
    :param items: List of mint items.
    :param batch_size: Max items per batch.
    :param build_ref: Function to build mint ref from item.
    :return: Summary of minted items.
    """
    batch_size = min(batch_size, 249)
    total = len(items)
    minted = 0
    results = []

    while minted < total:
        from_index = await _get_next_item_index(app_ctx, collection_address)
        batch_items = items[minted : minted + batch_size]
        batch_count = len(batch_items)

        refs = []
        for i, item in enumerate(batch_items):
            refs.append(build_ref(item, from_index + i))

        body = NFTCollectionBatchMintItemBody(
            items_refs=refs,
            from_index=from_index,
            forward_amount=FORWARD_MINT_NFT,
        )

        result = await app_ctx.sender.send(
            [
                SendMessage(
                    destination=collection_address,
                    amount=GAS_MINT_NFT * batch_count,
                    body=body.serialize(),
                )
            ],
        )

        results.append(result)

        expected_index = from_index + batch_count
        confirmed = await _wait_batch_confirmation(
            app_ctx,
            collection_address,
            expected_index,
        )

        if not confirmed:
            raise ToolError(
                f"Batch confirmation timeout. "
                f"Expected next_item_index={expected_index}, "
                f"minted so far: {minted + batch_count}. "
                f"Last hash: {result.normalized_hash}"
            )

        minted += batch_count

        await ctx.report_progress(
            progress=minted,
            total=total,
            message=f"Minted {minted}/{total} items",
        )

    return BatchMintResult(
        total=total,
        batches=[r.explorer_url for r in results],
    )


async def _wait_batch_confirmation(
    app_ctx: AppContext,
    collection_address: str,
    expected_index: int,
    timeout: int = 60,
) -> bool:
    """Wait for batch mint confirmation by polling next_item_index.

    :param app_ctx: Application context.
    :param collection_address: Collection address.
    :param expected_index: Expected next_item_index after batch.
    :param timeout: Max wait time in seconds.
    :return: True if confirmed, False if timed out.
    """
    elapsed = 0
    while elapsed < timeout:
        current_index = await _get_next_item_index(app_ctx, collection_address)
        if current_index >= expected_index:
            return True
        await asyncio.sleep(3)
        elapsed += 3
    return False
