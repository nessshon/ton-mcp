from __future__ import annotations

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import ContractInfoResult
from ton_mcp.utils import fetch_contract_info


async def get_contract_info(
    address: str,
    app_ctx: AppContext = APP_CTX,
) -> ContractInfoResult:
    """Get balance, state, and last transaction for any TON address."""
    return await fetch_contract_info(app_ctx, address)
