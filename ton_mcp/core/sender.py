from __future__ import annotations

import time
import typing as t

from pytoniq_core import Address
from tonutils.exceptions import ContractError
from tonutils.tonconnect.models.payload import SendTransactionPayload
from tonutils.utils import to_amount

from ton_mcp.constants import GAS_RESERVE
from ton_mcp.models import TransactionResult
from ton_mcp.types import SendMessage, SendResult, SignMethod
from ton_mcp.utils.transaction import confirm_transaction

if t.TYPE_CHECKING:
    from fastmcp import Context
    from ton_mcp.core.config import Config
    from ton_mcp.core.context import AppContext
    from tonutils.clients.protocol import ClientProtocol
    from tonutils.contracts.wallet.base import BaseWallet
    from tonutils.tonconnect.connector import Connector
    from tonutils.types import ContractInfo


def format_send_result(label: str, count: int, result: SendResult) -> TransactionResult:
    """Build a transaction result for tool output.

    :param label: Operation label (e.g. "TON transfer").
    :param count: Number of messages sent.
    :param result: Confirmed send result.
    :return: Transaction result model.
    """
    return TransactionResult(
        status="confirmed",
        hash=result.normalized_hash,
        explorer=result.explorer_url,
        label=label,
        messages=count,
    )


class Sender:
    """Single point for identity, validation, dispatch, and confirmation.

    Encapsulates wallet address resolution, balance checks, message
    count validation, and dispatch routing (SECRET_KEY / TONCONNECT).
    """

    def __init__(self, app_ctx: AppContext) -> None:
        self._app_ctx = app_ctx
        self._address: t.Optional[str] = None
        self._max_messages: t.Optional[int] = None

    @property
    def client(self) -> ClientProtocol:
        """Blockchain client."""
        return self._app_ctx.client

    @property
    def config(self) -> Config:
        """Server configuration."""
        return self._app_ctx.config

    async def get_address(self) -> str:
        """Resolve wallet address. Cached after first call.

        :return: Non-bounceable address string.
        :raises ValueError: If no wallet configured or connected.
        """
        if self._address is None:
            self._address = await self._resolve_address()
        return self._address

    async def get_max_messages(self) -> int:
        """Resolve max messages per transaction. Cached after first call.

        :return: Maximum number of messages the wallet supports.
        """
        if self._max_messages is None:
            self._max_messages = await self._resolve_max_messages()
        return self._max_messages

    def set_wallet(self, wallet: BaseWallet) -> None:
        """Load a wallet (from create_wallet tool). Resets caches.

        :param wallet: Wallet instance to activate.
        """
        self._app_ctx.wallet = wallet
        self._address = None
        self._max_messages = wallet.MAX_MESSAGES

    async def send(
        self,
        messages: t.List[SendMessage],
        ctx: t.Optional[Context] = None,
    ) -> SendResult:
        """Send messages: validate -> balance -> dispatch -> confirm.

        :param messages: One or more messages to send.
        :param ctx: Optional FastMCP context for progress reporting.
        :return: Confirmed send result with hash and explorer URL.
        :raises ValueError: If validation, balance, or sending fails.
        """
        if self._max_messages is None:
            self._max_messages = await self._resolve_max_messages()

        if len(messages) > self._max_messages:
            raise ValueError(
                f"Too many messages: {len(messages)}, "
                f"wallet supports max {self._max_messages}."
            )

        address_str = await self.get_address()
        address = Address(address_str)
        info = await self._app_ctx.client.get_info(address)
        self._check_balance(info, messages, address_str)

        normalized_hash = await self._dispatch(messages, ctx)

        return await confirm_transaction(
            client=self._app_ctx.client,
            address=address,
            normalized_hash=normalized_hash,
            network=self._app_ctx.config.network,
            explorer=self._app_ctx.config.explorer,
            ctx=ctx,
            last_transaction_lt=info.last_transaction_lt,
            last_transaction_hash=info.last_transaction_hash,
        )

    @staticmethod
    def _check_balance(
        info: ContractInfo,
        messages: t.List[SendMessage],
        address: str,
    ) -> None:
        """Verify wallet has sufficient balance for messages."""
        if not messages:
            return

        total = sum(int(m.amount) for m in messages)
        if total == 0:
            return

        required = total + GAS_RESERVE
        if info.balance < required:
            raise ValueError(
                f"Insufficient balance: have {to_amount(info.balance)} TON, "
                f"need ~{to_amount(required)} TON ({to_amount(total)} + fees).\n"
                f"Top up address: {address}"
            )

    @property
    def _is_secret_key(self) -> bool:
        """True when config has wallet_secret OR wallet was created dynamically."""
        return (
            self._app_ctx.config.sign_method == SignMethod.SECRET_KEY
            or self._app_ctx.wallet is not None
        )

    async def _get_connector(self) -> Connector:
        """Get or restore TonConnect connector."""
        from ton_mcp.constants import TONCONNECT_SESSION_KEY

        connector = self._app_ctx.tc.connectors.get(TONCONNECT_SESSION_KEY)
        if connector is None or not connector.connected:
            connector = self._app_ctx.tc.create_connector(TONCONNECT_SESSION_KEY)
            if not await connector.restore():
                raise ValueError(
                    "No wallet connected. Use connect_wallet or create_wallet."
                )
        return connector

    async def _dispatch(
        self,
        messages: t.List[SendMessage],
        ctx: t.Optional[Context] = None,
    ) -> str:
        """Route messages to SECRET_KEY or TONCONNECT dispatch."""
        if self._is_secret_key:
            if ctx:
                await ctx.info("Sending transaction...")
            return await self._dispatch_secret_key(messages)

        connector = await self._get_connector()
        wallet_name = connector.app_wallet.name if connector.app_wallet else "wallet"
        if ctx:
            await ctx.info(f"Approve the transaction in {wallet_name}.")
        return await self._dispatch_tonconnect(messages, connector)

    async def _dispatch_secret_key(self, messages: t.List[SendMessage]) -> str:
        """Send via wallet secret key."""
        wallet_msgs = [m.to_wallet_message() for m in messages]
        wallet = self._app_ctx.wallet
        if wallet is None:
            raise RuntimeError(
                "No wallet configured for SECRET_KEY dispatch."
            )
        try:
            msg = await wallet.batch_transfer_message(wallet_msgs)
        except ContractError as e:
            raise ValueError(str(e)) from e
        return msg.normalized_hash

    @staticmethod
    async def _dispatch_tonconnect(
        messages: t.List[SendMessage],
        connector: Connector,
    ) -> str:
        """Send via TonConnect wallet."""
        tc_msgs = [m.to_tc_message() for m in messages]
        valid_until = int(time.time()) + 300
        tc_payload = SendTransactionPayload(
            valid_until=valid_until,
            messages=tc_msgs,
        )
        request_id = await connector.send_transaction(tc_payload, timeout=valid_until)
        result, error = await connector.wait_transaction(request_id)
        if error is not None:
            raise ValueError(str(error))
        return result.normalized_hash

    async def _resolve_address(self) -> str:
        """Resolve wallet address based on signing mode."""
        if self._is_secret_key:
            if self._app_ctx.wallet is None:
                raise ValueError(
                    "No wallet configured. Use create_wallet or connect_wallet."
                )
            return self._app_ctx.wallet.address.to_str(is_bounceable=False)
        connector = await self._get_connector()
        return connector.account.address.to_str(is_bounceable=False)

    async def _resolve_max_messages(self) -> int:
        """Resolve max messages from wallet or TonConnect features."""
        if self._is_secret_key:
            if self._app_ctx.wallet is not None:
                return self._app_ctx.wallet.MAX_MESSAGES
            return 4
        connector = await self._get_connector()
        if connector.app_wallet:
            from tonutils.tonconnect.models.feature import (
                SendTransactionFeature,
            )

            for feature in connector.app_wallet.features:
                if isinstance(feature, SendTransactionFeature):
                    if feature.max_messages is not None:
                        return feature.max_messages
        return 4
