from __future__ import annotations

import typing as t

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import DeployResult
from tonutils.contracts import (
    NFTCollectionContent,
    NFTCollectionData,
    NFTCollectionEditable,
    NFTCollectionStandard,
    NFTItemEditable,
    NFTItemSoulbound,
    NFTItemStandard,
    OffchainCommonContent,
    OffchainContent,
    RoyaltyParams,
)
from tonutils.contracts.base import BaseContract

from ton_mcp.constants import GAS_TRANSFER


async def deploy_standard_collection(
    owner_address: str,
    collection_uri: str,
    items_prefix_uri: str,
    royalty_address: str,
    royalty: int = 50,
    royalty_denominator: int = 1000,
    app_ctx: AppContext = APP_CTX,
) -> DeployResult:
    """Deploy a standard NFT collection. Irreversible.

    Standard NFTs are immutable and freely transferable.
    ``collection_uri``: full URL to metadata JSON (name, description, image).
    ``items_prefix_uri``: base URL for items, must end with ``/``.
    Royalty is a fraction (default 50/1000 = 5%), not a percentage.
    """
    return await _deploy_collection(
        app_ctx=app_ctx,
        owner_address=owner_address,
        collection_uri=collection_uri,
        items_prefix_uri=items_prefix_uri,
        royalty_address=royalty_address,
        royalty=royalty,
        royalty_denominator=royalty_denominator,
        item_code_cls=NFTItemStandard,
        collection_cls=NFTCollectionStandard,
    )


async def deploy_soulbound_collection(
    owner_address: str,
    collection_uri: str,
    items_prefix_uri: str,
    royalty_address: str,
    royalty: int = 50,
    royalty_denominator: int = 1000,
    app_ctx: AppContext = APP_CTX,
) -> DeployResult:
    """Deploy a soulbound NFT collection (SBT). Irreversible.

    SBTs are non-transferable. Authority can revoke; owner can destroy.
    See ``deploy_standard_collection`` for parameter details.
    """
    return await _deploy_collection(
        app_ctx=app_ctx,
        owner_address=owner_address,
        collection_uri=collection_uri,
        items_prefix_uri=items_prefix_uri,
        royalty_address=royalty_address,
        royalty=royalty,
        royalty_denominator=royalty_denominator,
        item_code_cls=NFTItemSoulbound,
        collection_cls=NFTCollectionStandard,
    )


async def deploy_editable_collection(
    owner_address: str,
    collection_uri: str,
    items_prefix_uri: str,
    royalty_address: str,
    royalty: int = 50,
    royalty_denominator: int = 1000,
    app_ctx: AppContext = APP_CTX,
) -> DeployResult:
    """Deploy an editable NFT collection. Irreversible.

    Editor can modify item metadata after minting. Items are transferable.
    See ``deploy_standard_collection`` for parameter details.
    """
    return await _deploy_collection(
        app_ctx=app_ctx,
        owner_address=owner_address,
        collection_uri=collection_uri,
        items_prefix_uri=items_prefix_uri,
        royalty_address=royalty_address,
        royalty=royalty,
        royalty_denominator=royalty_denominator,
        item_code_cls=NFTItemEditable,
        collection_cls=NFTCollectionEditable,
    )


async def _deploy_collection(
    app_ctx: AppContext,
    owner_address: str,
    collection_uri: str,
    items_prefix_uri: str,
    royalty_address: str,
    royalty: int,
    royalty_denominator: int,
    item_code_cls: t.Type[BaseContract],
    collection_cls: t.Type[BaseContract],
) -> DeployResult:
    """Deploy an NFT collection contract.

    :param app_ctx: Application context.
    :param owner_address: Collection owner address.
    :param collection_uri: Collection metadata URI.
    :param items_prefix_uri: Item metadata URI prefix.
    :param royalty_address: Royalty recipient address.
    :param royalty: Royalty numerator.
    :param royalty_denominator: Royalty denominator.
    :param item_code_cls: NFT item class for code cell.
    :param collection_cls: NFT collection class for deployment.
    :return: Formatted deployment result string.
    """
    if items_prefix_uri and not items_prefix_uri.endswith("/"):
        items_prefix_uri += "/"

    nft_item_code = item_code_cls.get_default_code()
    content = NFTCollectionContent(
        content=OffchainContent(uri=collection_uri),
        common_content=OffchainCommonContent(prefix_uri=items_prefix_uri),
    )
    royalty_params = RoyaltyParams(
        royalty=royalty,
        denominator=royalty_denominator,
        address=royalty_address,
    )

    data = NFTCollectionData(
        owner_address=owner_address,
        content=content,
        royalty_params=royalty_params,
        nft_item_code=nft_item_code,
    )

    collection = collection_cls.from_data(
        client=app_ctx.client,
        data=data.serialize(),
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection.address,
                amount=GAS_TRANSFER,
                state_init=collection.state_init,
            )
        ],
    )

    return DeployResult(
        address=collection.address.to_str(is_bounceable=True),
        hash=result.normalized_hash,
        explorer=result.explorer_url,
    )
