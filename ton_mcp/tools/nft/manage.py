from __future__ import annotations

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import TransactionResult
from ton_mcp.core.sender import format_send_result
from tonutils.contracts import (
    NFTCollectionChangeContentBody,
    NFTCollectionChangeOwnerBody,
    NFTCollectionContent,
    NFTDestroyBody,
    NFTEditContentBody,
    NFTRevokeBody,
    NFTTransferEditorshipBody,
    OffchainCommonContent,
    OffchainContent,
    OffchainItemContent,
    RoyaltyParams,
)
from ton_mcp.constants import GAS_TRANSFER


async def revoke_soulbound_nft(
    nft_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Revoke a soulbound NFT. Irreversible.

    Authority-only. SBT stays on-chain but is marked invalid.
    """
    body = NFTRevokeBody()

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("SBT revoked", 1, result)


async def destroy_soulbound_nft(
    nft_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Permanently delete a soulbound NFT contract. IRREVERSIBLE.

    Owner-only (not authority).
    """
    body = NFTDestroyBody()

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("SBT destroyed", 1, result)


async def edit_nft_content(
    nft_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Update editable NFT metadata. Irreversible. Editor-only."""
    body = NFTEditContentBody(
        content=OffchainItemContent(suffix_uri=content_uri),
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("NFT content updated", 1, result)


async def transfer_nft_editorship(
    nft_address: str,
    new_editor_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Transfer editor role of an editable NFT. Irreversible. Current editor only."""
    my_address = await app_ctx.sender.get_address()

    body = NFTTransferEditorshipBody(
        editor_address=new_editor_address,
        response_address=my_address,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=nft_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Editorship transferred", 1, result)


async def change_collection_owner(
    collection_address: str,
    new_owner_address: str,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Transfer collection ownership. Irreversible.

    New owner controls minting. New owner can transfer back.
    """
    body = NFTCollectionChangeOwnerBody(owner_address=new_owner_address)

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Collection ownership transferred", 1, result)


async def change_collection_content(
    collection_address: str,
    collection_uri: str,
    items_prefix_uri: str,
    royalty_address: str,
    royalty: int = 50,
    royalty_denominator: int = 1000,
    app_ctx: AppContext = APP_CTX,
) -> TransactionResult:
    """Update collection metadata and royalty. Irreversible.

    Owner-only. Changing ``items_prefix_uri`` affects all existing items.
    """
    content = NFTCollectionContent(
        content=OffchainContent(uri=collection_uri),
        common_content=OffchainCommonContent(prefix_uri=items_prefix_uri),
    )
    royalty_params = RoyaltyParams(
        royalty=royalty,
        denominator=royalty_denominator,
        address=royalty_address,
    )

    body = NFTCollectionChangeContentBody(
        content=content,
        royalty_params=royalty_params,
    )

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=collection_address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
            )
        ],
    )

    return format_send_result("Collection content updated", 1, result)
