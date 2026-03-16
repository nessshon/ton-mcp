from __future__ import annotations

from fastmcp.exceptions import ToolError

from ton_mcp.constants import WALLET_VERSIONS
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import CreateWalletResult


async def create_wallet(
    version: str = "v5r1",
    app_ctx: AppContext = APP_CTX,
) -> CreateWalletResult:
    """Create a new TON wallet for this session.

    Session-only unless user saves mnemonic or private key to WALLET_SECRET in .env.
    Both are visible in response — show both and advise user to save securely.
    """
    wallet_cls = WALLET_VERSIONS.get(version)
    if wallet_cls is None:
        available = ", ".join(WALLET_VERSIONS.keys())
        raise ToolError(f"Unknown wallet version: {version}. Available: {available}")

    wallet, public_key, private_key, mnemonic = wallet_cls.create(app_ctx.client)
    app_ctx.sender.set_wallet(wallet)

    return CreateWalletResult(
        version=version,
        address=wallet.address.to_str(is_bounceable=False),
        private_key=private_key.as_b64,
        mnemonic=" ".join(mnemonic),
    )
