from __future__ import annotations

import typing as t

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from ton_mcp.core.config import config
from ton_mcp.core.context import AppContext
from ton_mcp.core.factory import (
    create_client,
    create_sender,
    create_tonconnect,
    restore_wallet,
)
from ton_mcp.types import SignMethod


@lifespan
async def app_lifespan(_server: FastMCP) -> t.AsyncIterator[dict[str, t.Any]]:
    """Manage application lifecycle.

    Creates client, wallet (if SECRET_KEY mode), and TonConnect manager.
    Yields application context shared across all tools.
    """
    client = create_client(config)
    await client.connect()

    wallet = None
    if config.sign_method == SignMethod.SECRET_KEY:
        wallet = restore_wallet(client, config)

    tc = create_tonconnect(config)

    try:
        app_ctx = AppContext(
            config=config,
            client=client,
            tc=tc,
            wallet=wallet,
        )
        app_ctx.sender = create_sender(app_ctx)
        yield {"app": app_ctx}
    finally:
        await tc.close_all()
        await client.close()
