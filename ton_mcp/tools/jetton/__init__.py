from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from ton_mcp.tools.jetton.deploy import deploy_jetton_master
from ton_mcp.tools.jetton.info import get_jetton_balance, get_jetton_info
from ton_mcp.tools.jetton.manage import (
    burn_jetton,
    change_jetton_admin,
    change_jetton_content,
    drop_jetton_admin,
)
from ton_mcp.tools.jetton.mint import mint_jetton
from ton_mcp.types import ACTION_ANNOTATIONS, QUERY_ANNOTATIONS


def setup_jetton_tools(mcp: FastMCP) -> None:
    """Register jetton tools."""
    mcp.add_tool(
        FunctionTool.from_function(
            get_jetton_info,
            annotations=QUERY_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            get_jetton_balance,
            annotations=QUERY_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            deploy_jetton_master,
            annotations=ACTION_ANNOTATIONS,
        ),
    )
    mcp.add_tool(
        FunctionTool.from_function(
            mint_jetton,
            annotations=ACTION_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            burn_jetton,
            annotations=ACTION_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            change_jetton_admin,
            annotations=ACTION_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            change_jetton_content,
            annotations=ACTION_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            drop_jetton_admin,
            annotations=ACTION_ANNOTATIONS,
        )
    )
