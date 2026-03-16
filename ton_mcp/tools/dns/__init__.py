from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from ton_mcp.tools.dns.info import get_dns_records, resolve_domain
from ton_mcp.tools.dns.manage import delete_dns_wallet_record, set_dns_wallet_record
from ton_mcp.types import ACTION_ANNOTATIONS, QUERY_ANNOTATIONS


def setup_dns_tools(mcp: FastMCP) -> None:
    """Register DNS tools."""
    mcp.add_tool(
        FunctionTool.from_function(
            resolve_domain,
            annotations=QUERY_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            get_dns_records,
            annotations=QUERY_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            set_dns_wallet_record,
            annotations=ACTION_ANNOTATIONS,
        )
    )
    mcp.add_tool(
        FunctionTool.from_function(
            delete_dns_wallet_record,
            annotations=ACTION_ANNOTATIONS,
        )
    )
