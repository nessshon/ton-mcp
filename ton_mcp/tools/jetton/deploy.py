from __future__ import annotations

from tonutils.contracts import (
    JettonMasterStablecoinData,
    JettonMasterStablecoinV2,
    JettonTopUpBody,
    JettonWalletStablecoinV2,
    OffchainContent,
)
from ton_mcp.constants import GAS_TRANSFER
from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.types import SendMessage
from ton_mcp.models import DeployResult


async def deploy_jetton_master(
    admin_address: str,
    content_uri: str,
    app_ctx: AppContext = APP_CTX,
) -> DeployResult:
    """Deploy a new jetton (fungible token). Irreversible.

    ``content_uri`` must point to JSON with: name, symbol, decimals, image.
    Initial supply is 0 — use ``mint_jetton`` to mint.
    """
    jetton_wallet_code = JettonWalletStablecoinV2.get_default_code()
    content = OffchainContent(uri=content_uri)

    data = JettonMasterStablecoinData(
        admin_address=admin_address,
        content=content,
        jetton_wallet_code=jetton_wallet_code,
    )

    jetton_master = JettonMasterStablecoinV2.from_data(
        client=app_ctx.client,
        data=data.serialize(),
    )

    body = JettonTopUpBody()

    result = await app_ctx.sender.send(
        [
            SendMessage(
                destination=jetton_master.address,
                amount=GAS_TRANSFER,
                body=body.serialize(),
                state_init=jetton_master.state_init,
            )
        ],
    )

    return DeployResult(
        address=jetton_master.address.to_str(is_bounceable=True),
        hash=result.normalized_hash,
        explorer=result.explorer_url,
    )
