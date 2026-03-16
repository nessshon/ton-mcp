from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from ton_mcp.tools.transfer.batch import (
    batch_send_jetton,
    batch_send_nft,
    batch_send_ton,
)
from ton_mcp.tools.transfer.single import (
    gasless_transfer,
    send_encrypted,
    send_jetton,
    send_nft,
    send_raw,
    send_ton,
)
from ton_mcp.types import ACTION_ANNOTATIONS


def setup_transfer_tools(mcp: FastMCP) -> None:
    """Register all transfer tools."""
    for fn in (
        send_ton,
        send_jetton,
        send_nft,
        send_encrypted,
        gasless_transfer,
        send_raw,
        batch_send_ton,
        batch_send_jetton,
        batch_send_nft,
    ):
        mcp.add_tool(
            FunctionTool.from_function(
                fn,
                annotations=ACTION_ANNOTATIONS,
            ),
        )
