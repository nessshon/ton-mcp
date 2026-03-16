from __future__ import annotations

import argparse

from fastmcp import FastMCP

from ton_mcp import __version__
from ton_mcp.core import INSTRUCTIONS, app_lifespan, config
from ton_mcp.tools import setup_tools

mcp = FastMCP(
    "TON MCP",
    lifespan=app_lifespan,
    instructions=INSTRUCTIONS,
    on_duplicate="error",
)


def main() -> None:
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(prog="ton-mcp")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
    )
    args = parser.parse_args()

    setup_tools(mcp, config)

    run_kwargs: dict[str, object] = {"transport": args.transport}
    if args.transport != "stdio":
        run_kwargs["host"] = config.mcp_server_host
        run_kwargs["port"] = config.mcp_server_port

    mcp.run(**run_kwargs)


if __name__ == "__main__":
    main()
