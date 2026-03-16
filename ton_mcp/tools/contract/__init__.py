from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from ton_mcp.tools.contract.info import get_contract_info
from ton_mcp.types import QUERY_ANNOTATIONS


def setup_contract_tools(mcp: FastMCP) -> None:
    """Register contract tools."""
    mcp.add_tool(
        FunctionTool.from_function(
            get_contract_info,
            annotations=QUERY_ANNOTATIONS,
        )
    )
