from __future__ import annotations

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import ContractInfoResult
from ton_mcp.utils import fetch_contract_info


async def get_my_wallet_info(app_ctx: AppContext = APP_CTX) -> ContractInfoResult:
    """Get balance, state, sign method, and max messages for the connected wallet."""
    address = await app_ctx.sender.get_address()
    result = await fetch_contract_info(app_ctx, address)
    result.sign_method = app_ctx.config.sign_method.value
    result.network = app_ctx.config.network.name.lower()
    result.max_messages = await app_ctx.sender.get_max_messages()
    return result
