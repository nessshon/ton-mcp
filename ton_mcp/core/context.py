from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from fastmcp.dependencies import Depends
from fastmcp.server.dependencies import get_context

from ton_mcp.core.config import Config
from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.tonconnect import TonConnect

if t.TYPE_CHECKING:
    from ton_mcp.core.sender import Sender


@dataclass
class AppContext:
    """Application context shared across all tools."""

    config: Config
    tc: TonConnect
    client: ClientProtocol
    wallet: t.Optional[BaseWallet] = field(default=None)
    sender: Sender = field(init=False)


def _get_app_ctx() -> AppContext:
    """Extract AppContext from lifespan context.

    :return: Application context.
    """
    ctx = get_context()
    return ctx.lifespan_context["app"]


APP_CTX = Depends(_get_app_ctx)
"""Dependency for injecting AppContext into tool functions."""
