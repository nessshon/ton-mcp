from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from ton_mcp.tools.nft.deploy import (
    deploy_editable_collection,
    deploy_soulbound_collection,
    deploy_standard_collection,
)
from ton_mcp.tools.nft.info import get_collection_info, get_nft_info
from ton_mcp.tools.nft.manage import (
    change_collection_content,
    change_collection_owner,
    destroy_soulbound_nft,
    edit_nft_content,
    revoke_soulbound_nft,
    transfer_nft_editorship,
)
from ton_mcp.tools.nft.mint import (
    batch_mint_editable_nft,
    batch_mint_nft,
    batch_mint_soulbound_nft,
    mint_editable_nft,
    mint_nft,
    mint_soulbound_nft,
)
from ton_mcp.types import ACTION_ANNOTATIONS, QUERY_ANNOTATIONS


def setup_nft_tools(mcp: FastMCP) -> None:
    """Register NFT tools."""
    mcp.add_tool(
        FunctionTool.from_function(
            get_collection_info,
            annotations=QUERY_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            get_nft_info,
            annotations=QUERY_ANNOTATIONS,
        ),
    )
    for fn in (
        deploy_standard_collection,
        deploy_soulbound_collection,
        deploy_editable_collection,
        mint_nft,
        mint_soulbound_nft,
        mint_editable_nft,
        batch_mint_nft,
        batch_mint_soulbound_nft,
        batch_mint_editable_nft,
        revoke_soulbound_nft,
        destroy_soulbound_nft,
        edit_nft_content,
        transfer_nft_editorship,
        change_collection_owner,
        change_collection_content,
    ):
        mcp.add_tool(
            FunctionTool.from_function(
                fn,
                annotations=ACTION_ANNOTATIONS,
            ),
        )
