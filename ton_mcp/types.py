from __future__ import annotations

import enum
import typing as t
from dataclasses import dataclass

from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict
from pytoniq_core import Address, Cell, StateInit
from pytoniq_core import WalletMessage
from tonutils.contracts.wallet.messages import InternalMessage
from tonutils.contracts.wallet.tlb import TextCommentBody
from tonutils.tonconnect.models.payload import SendTransactionMessage
from tonutils.types import DEFAULT_SENDMODE, AddressLike

ACTION_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)
"""Tool annotations for action (mutating) tools."""

QUERY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=True,
)
"""Tool annotations for read-only query tools."""


@dataclass(frozen=True)
class NetworkCapabilities:
    """Per-network feature constraints."""

    supported_providers: t.FrozenSet[str]
    supported_explorers: t.FrozenSet[str]
    excluded_tools: t.FrozenSet[str] = frozenset()


class SignMethod(enum.Enum):
    """Transaction signing method: SECRET_KEY for automatic or TONCONNECT for user-approved."""

    SECRET_KEY = "secret_key"
    TONCONNECT = "tonconnect"


class SendMessage(BaseModel):
    """Internal message for Sender. Not exposed to AI.

    :param destination: Resolved TON address or Address object.
    :param amount: Amount in nanotons (int).
    :param body: Message body: text comment (str) or serialized Cell.
    :param state_init: Optional state init for contract deployment.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    destination: AddressLike
    amount: int
    body: t.Optional[t.Union[Cell, str]] = None
    state_init: t.Optional[StateInit] = None

    def to_wallet_message(self) -> WalletMessage:
        """Convert to WalletMessage for SECRET_KEY dispatch."""
        body = (
            TextCommentBody(self.body).serialize()
            if isinstance(self.body, str)
            else self.body
        )
        return WalletMessage(
            send_mode=DEFAULT_SENDMODE,
            message=InternalMessage(
                dest=self.destination,
                value=self.amount,
                body=body,
                state_init=self.state_init,
            ),
        )

    def to_tc_message(self) -> SendTransactionMessage:
        """Convert to SendTransactionMessage for TONCONNECT dispatch."""
        dest = (
            Address(self.destination)
            if isinstance(self.destination, str)
            else self.destination
        )
        payload = (
            TextCommentBody(self.body).serialize()
            if isinstance(self.body, str)
            else self.body
        )
        return SendTransactionMessage(
            address=dest,
            amount=self.amount,
            state_init=self.state_init,
            payload=payload,
        )


class SendResult(BaseModel):
    """Result of a confirmed transaction.

    :param normalized_hash: Hex-encoded normalized transaction hash.
    :param explorer_url: Full URL to view the transaction in the block explorer.
    """

    normalized_hash: str
    explorer_url: str
