from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool
from mcp.types import ToolAnnotations

from ton_mcp.tools.wallet.info import get_my_wallet_info
from ton_mcp.tools.wallet.manage import create_wallet
from ton_mcp.types import QUERY_ANNOTATIONS

CREATE_WALLET_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)


def setup_wallet_tools(mcp: FastMCP) -> None:
    """Register wallet tools."""
    mcp.add_tool(
        FunctionTool.from_function(
            get_my_wallet_info,
            annotations=QUERY_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            create_wallet,
            annotations=CREATE_WALLET_ANNOTATIONS,
        ),
    )
