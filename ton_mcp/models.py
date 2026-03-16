from __future__ import annotations

import typing as t

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base class for all tool responses.

    :param hint: Optional display hint for AI client.
    """

    hint: t.Optional[str] = None


class TonTransfer(BaseModel):
    """Single TON transfer for batch operations.

    :param destination: Recipient address or .ton/.t.me domain.
    :param amount: Amount in TON (e.g. "1.5").
    :param comment: Optional text comment.
    """

    destination: str = Field(
        description="TON address (UQ.../EQ...) or .ton/.t.me domain"
    )
    amount: str = Field(description='Amount in TON (e.g. "1.5")')
    comment: str = Field(default="", description="Optional text comment")


class JettonTransfer(BaseModel):
    """Single jetton transfer for batch operations.

    :param destination: Recipient address or .ton/.t.me domain.
    :param jetton_master_address: Jetton master contract address.
    :param amount: Jetton amount in human-readable format (e.g. "10.5").
    :param decimals: Token decimal places (default: 9).
    :param comment: Optional text comment.
    """

    destination: str = Field(description="Recipient TON address or .ton/.t.me domain")
    jetton_master_address: str = Field(description="Jetton master contract address")
    amount: str = Field(
        description='Jetton amount in human-readable format (e.g. "10.5")'
    )
    decimals: int = Field(
        default=9, description="Token decimal places (6 for USDT, 9 for most)"
    )
    comment: str = Field(default="", description="Optional text comment")


class NFTTransfer(BaseModel):
    """Single NFT transfer for batch operations.

    :param destination: New owner address or .ton/.t.me domain.
    :param nft_address: NFT item contract address.
    :param comment: Optional text comment.
    """

    destination: str = Field(description="New owner TON address or .ton/.t.me domain")
    nft_address: str = Field(description="NFT item contract address (EQ.../UQ...)")
    comment: str = Field(default="", description="Optional text comment")


class RawMessage(BaseModel):
    """Single raw message for send_raw.

    :param destination: Recipient TON address.
    :param amount: Amount in nanotons as string (e.g. "500000000" = 0.5 TON).
    :param body: Payload: text comment, or serialized Cell as hex or base64.
    :param state_init: Contract state init as hex or base64.
    """

    destination: str = Field(
        description="Recipient TON address (EQ.../UQ.../0:...)",
    )
    amount: str = Field(
        description='Amount in nanotons as string (e.g. "500000000" = 0.5 TON)',
    )
    body: t.Optional[str] = Field(
        default=None,
        description="Payload: text comment, or serialized Cell as hex or base64",
    )
    state_init: t.Optional[str] = Field(
        default=None,
        description="Contract state init as hex or base64",
    )


class MintItem(BaseModel):
    """Single item for batch standard NFT mint.

    :param owner_address: Owner of the minted NFT.
    :param content_uri: Off-chain metadata URI suffix for the item.
    """

    owner_address: str = Field(description="Owner address (UQ.../EQ...)")
    content_uri: str = Field(
        description='Item metadata URI suffix (e.g. "0.json")',
    )


class SoulboundMintItem(MintItem):
    """Single item for batch soulbound NFT mint.

    :param authority_address: Authority that can revoke the SBT.
    """

    authority_address: str = Field(
        description="Authority address that can revoke the SBT (UQ.../EQ...)",
    )


class EditableMintItem(MintItem):
    """Single item for batch editable NFT mint.

    :param editor_address: Editor that can modify item content.
    """

    editor_address: str = Field(
        description="Editor address that can modify item metadata (UQ.../EQ...)",
    )


class TransactionResult(BaseResponse):
    """Result of a confirmed on-chain transaction.

    :param status: Transaction status ("confirmed" or "aborted").
    :param hash: Normalized transaction hash.
    :param explorer: Explorer URL for the transaction.
    :param label: Human-readable operation label (e.g. "TON transfer").
    :param messages: Number of messages in the transaction.
    """

    status: str = Field(
        description='Transaction status ("confirmed" or "aborted")',
    )
    hash: str = Field(description="Normalized transaction hash")
    explorer: str = Field(description="Explorer URL for the transaction")
    label: str = Field(
        description='Human-readable operation label (e.g. "TON transfer")',
    )
    messages: int = Field(
        description="Number of messages in the transaction",
    )


class DeployResult(BaseResponse):
    """Result of a contract deployment (jetton master, NFT collection, etc.).

    :param address: Deployed contract address.
    :param hash: Transaction hash.
    :param explorer: Explorer URL.
    """

    address: str = Field(description="Deployed contract address")
    hash: str = Field(description="Transaction hash")
    explorer: str = Field(description="Explorer URL")


class ContractInfoResult(BaseResponse):
    """On-chain contract information.

    :param address: Non-bounceable address.
    :param balance: Human-readable balance (e.g. "1.5 TON").
    :param balance_nano: Balance in nanotons.
    :param state: Contract state ("active", "frozen", "uninitialized").
    :param sign_method: Signing method (only set for own wallet info).
    :param network: Current network (only set for own wallet info).
    :param max_messages: Max messages per transaction (only set for own wallet info).
    :param last_transaction_lt: Last transaction logical time.
    :param last_transaction_hash: Last transaction hash.
    """

    address: str = Field(description="Non-bounceable address")
    balance: str = Field(
        description='Human-readable balance (e.g. "1.5 TON")',
    )
    balance_nano: int = Field(description="Balance in nanotons")
    state: str = Field(
        description='Contract state: "active", "frozen", or "uninitialized"',
    )
    sign_method: t.Optional[str] = None
    network: t.Optional[str] = None
    max_messages: t.Optional[int] = None
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None


class CreateWalletResult(BaseResponse):
    """Result of wallet creation.

    :param version: Wallet version (e.g. "v5r1").
    :param address: Non-bounceable wallet address.
    :param private_key: Private key in base64 format.
    :param mnemonic: Space-separated mnemonic words.
    """

    version: str
    address: str
    private_key: str
    mnemonic: str


class GaslessTransferResult(BaseResponse):
    """Result of a gasless jetton transfer.

    :param commission: Commission in base units deducted from jetton balance.
    """

    commission: str = Field(
        description="Commission deducted from jetton balance (base units)",
    )


class WalletInfoResult(BaseResponse):
    """Connected wallet information.

    :param wallet: Wallet app name.
    :param address: Non-bounceable wallet address.
    :param network: Network name.
    """

    wallet: str
    address: str
    network: str


class ConnectWalletResult(BaseResponse):
    """Result of connect_wallet: QR and wallet links.

    :param qr_code_link: URL that opens a QR code image for scanning.
    :param wallets: Mapping of wallet name to deep link.
    """

    qr_code_link: str
    wallets: t.Dict[str, str]


class JettonInfoResult(BaseResponse):
    """Jetton master contract information.

    :param address: Jetton master address.
    :param total_supply: Total supply in base units.
    :param total_supply_formatted: Human-readable total supply
        (only when decimals is known).
    :param mintable: Whether new tokens can be minted.
    :param admin: Admin address or None if dropped.
    :param name: Token name from metadata.
    :param symbol: Token symbol from metadata.
    :param decimals: Token decimal places from metadata.
    :param description: Token description from metadata.
    :param image: Token image URL from metadata.
    :param metadata: Full parsed metadata dict (TEP-64).
    """

    address: str
    total_supply: int
    total_supply_formatted: t.Optional[str] = None
    mintable: bool
    admin: t.Optional[str] = None
    name: t.Optional[str] = None
    symbol: t.Optional[str] = None
    decimals: t.Optional[int] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None
    metadata: t.Optional[t.Dict[str, t.Any]] = None


class JettonBalanceResult(BaseResponse):
    """Jetton balance for a wallet.

    :param owner: Owner wallet address.
    :param jetton_wallet: Jetton wallet contract address or None if not deployed.
    :param balance: Balance in base units.
    :param balance_formatted: Human-readable balance (only when decimals is known).
    :param decimals: Token decimal places from metadata.
    :param symbol: Token symbol from metadata.
    """

    owner: str
    jetton_wallet: t.Optional[str] = None
    balance: int
    balance_formatted: t.Optional[str] = None
    decimals: t.Optional[int] = None
    symbol: t.Optional[str] = None


class CollectionInfoResult(BaseResponse):
    """NFT collection information.

    :param address: Collection contract address.
    :param next_item_index: Next item index (= total minted).
    :param owner: Collection owner address.
    :param name: Collection name from metadata.
    :param description: Collection description from metadata.
    :param image: Collection image URL from metadata.
    :param content_uri: Original metadata URI (off-chain collections only).
    :param items_prefix_uri: Base URI prefix for item metadata.
    :param royalty_percent: Royalty as percentage (e.g. 5.0 for 5%).
    :param royalty_address: Address that receives royalty payments.
    :param metadata: Full parsed collection metadata dict (TEP-64).
    """

    address: str
    next_item_index: int
    owner: t.Optional[str] = None
    name: t.Optional[str] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None
    content_uri: t.Optional[str] = None
    items_prefix_uri: t.Optional[str] = None
    royalty_percent: t.Optional[float] = None
    royalty_address: t.Optional[str] = None
    metadata: t.Optional[t.Dict[str, t.Any]] = None


class NFTInfoResult(BaseResponse):
    """NFT item information.

    :param address: NFT item contract address.
    :param initialized: Whether the item is initialized.
    :param index: Item index in collection.
    :param collection: Collection contract address.
    :param owner: Current owner address.
    :param name: Item name from metadata.
    :param description: Item description from metadata.
    :param image: Item image URL from metadata.
    :param authority_address: SBT authority address (only for soulbound NFTs).
    :param revoked_at: SBT revocation unix timestamp, 0 if not revoked
        (only for soulbound NFTs).
    :param metadata: Full parsed item metadata dict (TEP-64).
    """

    address: str
    initialized: bool
    index: int
    collection: t.Optional[str] = None
    owner: t.Optional[str] = None
    name: t.Optional[str] = None
    description: t.Optional[str] = None
    image: t.Optional[str] = None
    authority_address: t.Optional[str] = None
    revoked_at: t.Optional[int] = None
    metadata: t.Optional[t.Dict[str, t.Any]] = None


class MintNFTResult(BaseResponse):
    """Result of single NFT mint.

    :param item_index: Minted item index.
    :param hash: Transaction hash.
    :param explorer: Explorer URL.
    """

    item_index: int
    hash: str
    explorer: str


class BatchMintResult(BaseResponse):
    """Result of batch NFT mint.

    :param total: Total items minted.
    :param batches: Explorer URLs per batch.
    """

    total: int
    batches: t.List[str]


class DomainResolveResult(BaseResponse):
    """Result of domain resolution.

    :param domain: Resolved domain name.
    :param category: Record category.
    :param value: Resolved value (address, hash, etc.).
    """

    domain: str
    category: str
    value: t.Optional[str] = None


class DNSRecordItem(BaseModel):
    """Single DNS record entry.

    :param category: Record category name.
    :param value: Record value.
    """

    category: str
    value: str


class DNSRecordsResult(BaseResponse):
    """All DNS records for a domain.

    :param domain: Domain name.
    :param owner: Domain owner address.
    :param records: List of DNS records.
    """

    domain: str
    owner: str
    records: t.List[DNSRecordItem]
