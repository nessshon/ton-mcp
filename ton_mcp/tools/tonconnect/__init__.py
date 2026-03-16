from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool
from mcp.types import ToolAnnotations

from ton_mcp.tools.tonconnect.manage import (
    await_wallet_connection,
    connect_wallet,
    disconnect_wallet,
)

CONNECT_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    openWorldHint=True,
)

DISCONNECT_ANNOTATIONS = ToolAnnotations(
    destructiveHint=True,
    openWorldHint=True,
)


def setup_tonconnect_tools(mcp: FastMCP) -> None:
    """Register TonConnect tools on the MCP server."""
    mcp.add_tool(
        FunctionTool.from_function(
            connect_wallet,
            annotations=CONNECT_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            await_wallet_connection,
            annotations=CONNECT_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            disconnect_wallet,
            annotations=DISCONNECT_ANNOTATIONS,
        ),
    )
