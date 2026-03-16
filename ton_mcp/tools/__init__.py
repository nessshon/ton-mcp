from __future__ import annotations

from fastmcp import FastMCP

from ton_mcp.core import Config, NETWORK_CAPABILITIES
from ton_mcp.tools.contract import setup_contract_tools
from ton_mcp.tools.dns import setup_dns_tools
from ton_mcp.tools.jetton import setup_jetton_tools
from ton_mcp.tools.nft import setup_nft_tools
from ton_mcp.tools.tonconnect import setup_tonconnect_tools
from ton_mcp.tools.transfer import setup_transfer_tools
from ton_mcp.tools.wallet import setup_wallet_tools
from ton_mcp.types import SignMethod


def setup_tools(mcp: FastMCP, config: Config) -> None:
    """Register all MCP tools based on configuration.

    :param mcp: FastMCP server instance.
    :param config: Application configuration.
    """
    setup_contract_tools(mcp)
    setup_dns_tools(mcp)
    setup_jetton_tools(mcp)
    setup_nft_tools(mcp)
    setup_transfer_tools(mcp)
    setup_wallet_tools(mcp)

    if config.sign_method == SignMethod.TONCONNECT:
        setup_tonconnect_tools(mcp)

    _exclude_tools(mcp, config)


def _exclude_tools(mcp: FastMCP, config: Config) -> None:
    """Remove tools not supported on the current network."""
    caps = NETWORK_CAPABILITIES.get(config.network)
    if caps is not None:
        for tool_name in caps.excluded_tools:
            mcp.remove_tool(tool_name)
