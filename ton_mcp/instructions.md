# TON MCP Server

MCP server for TON blockchain. Wallets, jettons, NFTs, DNS, batch transfers, TonConnect.

> Alpha — tool names and behavior may change. Test on testnet first.

## Critical Rules

- **Verify before assuming.** Call `get_my_wallet_info` before any claim about
  wallet capabilities (max messages, balance, version). Never guess.
- **Verify decimals.** Call `get_jetton_info` before any jetton operation to get
  the correct `decimals`. Wrong decimals silently sends the wrong amount.
  Never assume decimals=9. If metadata unavailable, ask the user.
- **Confirm before mutating.** Every transfer/mint/deploy is irreversible.
  Confirm with the user before sending.
- **Show explorer link.** Always present the explorer URL from transaction results.
- **Check before batch.** Call `get_my_wallet_info` first — it returns
  `max_messages`. The server rejects if exceeded.
- Amounts are always strings, never floats or ints.

## Amount Formats

| Context           | Format               | Example                               |
|-------------------|----------------------|---------------------------------------|
| TON transfers     | TON as string        | `"0.5"`, `"100"`                      |
| Jetton operations | Human-readable units | `"10.5"` (converted using `decimals`) |
| `send_raw`        | Nanotons as string   | `"500000000"` = 0.5 TON               |

## Addresses

- **UQ...** (non-bounceable) — for wallets. Use when sending to a new/undeployed wallet.
- **EQ...** (bounceable) — for smart contracts. Funds bounce back if contract can't process.
- **0:...** (raw) — no checksum. Avoid for user input.
- **.ton / .t.me** domains are accepted in `destination` parameters and resolved automatically.

## Wallet Setup

No wallet = no transactions. Two options:

**Option 1: Create new wallet** — call `create_wallet`. Default: v5r1.
Show both mnemonic and private_key from the response. Advise user to save
either one to WALLET_SECRET in .env (mnemonic or base64 private key both work).
New wallet is `uninitialized` until first outgoing tx (which deploys the contract).

**Option 2: Connect existing wallet** (TonConnect):

1. Call `connect_wallet`. If session exists, returns wallet info immediately (done).
2. If new connection: show **all** returned links with wallet names. QR code link opens a scannable image.
3. Immediately call `await_wallet_connection` — waits for user approval in wallet app.

### Signing Modes

|                    | SECRET_KEY                  | TonConnect                  |
|--------------------|-----------------------------|-----------------------------|
| Signing            | Automatic                   | User approves in wallet app |
| Encrypted messages | Yes                         | No                          |
| Gasless transfers  | Yes (v5r1, mainnet, tonapi) | No                          |

When using TonConnect, tell the user to open their wallet and approve.

## Wallet Versions

| Version         | Max msgs | Best for                                                                   |
|-----------------|----------|----------------------------------------------------------------------------|
| v5r1 (default)  | 255      | General use. Gasless (USDT fees), extensions, signature control            |
| v4r2            | 4        | Legacy dApps, plugin system (security risk)                                |
| v3r2            | 4        | Legacy. Most widely deployed, subwallet support                            |
| highload_v3r1   | 254      | Exchanges, mass payouts. Parallel query_id, bulletproof replay protection  |
| preprocessed_v2 | 255      | Cheapest gas (1537 units/tx). Mass sends, airdrops. Sequential, no gasless |

## TON Architecture (TEPs)

Key concepts that affect how tools work. Getting these wrong causes
silent failures or wrong results.

**Jettons (TEP-74):** Two-contract model — JettonMaster (metadata, supply, admin)

+ JettonWallet (one per owner, holds balance). Transfers go through sender's
  jetton wallet, not master. Balance exists only in wallet contracts.
  Admin-only ops (mint, change content) are silently rejected if caller is not admin.

**NFTs (TEP-62):** Each item = separate contract. Collection tracks
`next_item_index`. Item metadata = collection's `items_prefix_uri` +
item's `content_uri` suffix (resolved via `get_nft_content` on-chain).
Standalone items (no collection) store full metadata directly.

**SBT (TEP-85):** Transfer always rejected. Authority can revoke (sets
`revoked_at`, stays on-chain). Owner can destroy (deletes contract).
Both irreversible. Authority is set at mint time.

**Metadata (TEP-64):** Off-chain = `0x01` + URI to JSON. Semi-chain =
on-chain dict with `uri` key pointing to JSON; on-chain values override
off-chain on conflict. Required fields: jettons need `name`, `symbol`, `decimals`,
`description`, `image`; NFTs need `name`, `description`, `image`.

**Royalty (TEP-66):** Fraction `numerator / denominator`, NOT percentage.
Both uint16 (max 65535). Numerator must be less than denominator.

**DNS (TEP-81):** Domains are NFT-like contracts. Operations require the
contract address, not domain string. Categories: `wallet`, `site` (ADNL),
`storage` (bag ID), `dns_next_resolver`.

## Tool Notes

Tool parameters and return types are in JSON schemas. Below are only
non-obvious behaviors, gotchas, and workflows that schemas don't convey.

### Jettons

- `get_jetton_info` — **always call before send/mint/burn** to get `decimals`.
  Also check `admin` field before admin ops (`mint_jetton`, `change_jetton_admin`,
  `change_jetton_content`, `drop_jetton_admin`) — verify it matches connected wallet.
- Before `send_jetton` / `burn_jetton`, call `get_jetton_balance` to verify
  sufficient balance.
- Unverified ops waste gas — tx executes but the contract silently rejects.
- `deploy_jetton_master` — `content_uri` must point to JSON with:
  `name`, `symbol`, `decimals`, `description`, `image`. Initial supply = 0.
- `drop_jetton_admin` — **IRREVERSIBLE.** No one can mint or update metadata after this.

### NFTs

**Three collection types:** Standard (transferable, immutable), Soulbound/SBT
(non-transferable), Editable (transferable, metadata updatable).
If user doesn't specify, suggest Editable — most flexible.

**Deploy params:**

- `collection_uri` — full URL to collection metadata JSON.
- `items_prefix_uri` — base URL for items. **Must end with `/`.**
  Full item URL = `items_prefix_uri` + `content_uri` (e.g. `https://x.com/nft/` + `0.json`).

Before `send_nft`, call `get_nft_info` to verify ownership.
Before minting or collection management, call `get_collection_info` to verify
`owner` matches connected wallet.

**Mint:** `content_uri` is a **suffix** (e.g. `0.json`), not a full URL.
Index is auto-assigned.
Before minting, call `get_collection_info` to get `next_item_index` —
use it to generate correct `content_uri` suffixes (e.g. `"{index}.json"`).

**Batch mint:** pass all items in one call — the tool splits into batches
automatically (max 249 per tx, default batch_size=100). Do not split manually.
Large item arrays are slow to generate. Recommend smaller batches (10–50)
for faster response; scale up if the user explicitly needs more.

**Editable specifics:**

- `edit_nft_content` / `transfer_nft_editorship` — editor only.

**Collection management:**

- `change_collection_content` — changing `items_prefix_uri` affects **all existing items**.

### DNS

If user provides "name.ton" where NFT address is expected, explain they
need the contract address (look up on tonviewer.com).

### Transfers

- `send_encrypted` — **SECRET_KEY only.** Recipient must be deployed (active).
- `gasless_transfer` — **Mainnet only. Requires: v5r1 + SECRET_KEY + tonapi.**
  Commission deducted from jetton balance. Jetton must be relay-supported (e.g. USDT).
- `send_raw` — amounts in nanotons. Body: hex/base64 BOC or plain text (comment).

## Network Support

| Network | Providers               | Explorers          | Limitations        |
|---------|-------------------------|--------------------|--------------------|
| mainnet | toncenter, tonapi, lite | tonviewer, tonscan | —                  |
| testnet | toncenter, tonapi, lite | tonviewer, tonscan | —                  |
| tetra   | tonapi only             | tonviewer only     | No DNS, no gasless |

## Known Jettons

Addresses differ between networks. **Never use mainnet address on testnet or vice versa.**
Call `get_my_wallet_info` to confirm current network first.

### Mainnet

| Symbol | Decimals | Master address                                     |
|--------|----------|----------------------------------------------------|
| USDT   | 6        | `EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs` |
| NOT    | 9        | `EQAvlWFDxGF2lXm67y4yzC17wYKD9A0guwPkMs1gOsM__NOT` |

### Testnet

| Symbol | Decimals | Master address                                     |
|--------|----------|----------------------------------------------------|
| USDT   | 6        | `kQB0ZYUL5M3KfrW0tSnwdFO1nC-BQHC2gcZl-WaF2on_USDT` |
| NOT    | 9        | `kQBMfIaxfLQMP4h1Pg2V_AuyToC3jdB8MmA6u3bx8i1__NOT` |

### Getting Testnet Tokens

- **TON**: https://t.me/testgiver_ton_bot
- **USDT** (1000 per call):
  `send_raw([{destination: "kQB0ZYUL5M3KfrW0tSnwdFO1nC-BQHC2gcZl-WaF2on_USDT", amount: "100000000", body: "te6ccgEBAgEAKQABIWQrfQcAAAAAAAAAABAX14QCAQAlF41FGQAAAAAAAAAAQ7msoAAQFA=="}])`
- **NOT** (1000 per call):
  `send_raw([{destination: "kQBMfIaxfLQMP4h1Pg2V_AuyToC3jdB8MmA6u3bx8i1__NOT", amount: "100000000", body: "te6ccgEBAgEAKgABIWQrfQcAAAAAAAAAABAX14QCAQAnF41FGQAAAAAAAAAAXo1KUQAAEBQ="}])`
- Duplicate the message in the array to mint more (up to wallet's max messages).

## Error Patterns

| Error                                  | Action                                                                               |
|----------------------------------------|--------------------------------------------------------------------------------------|
| Insufficient balance                   | Error includes wallet address. Suggest top-up.                                       |
| No wallet                              | Suggest `create_wallet` or `connect_wallet`.                                         |
| SECRET_KEY required                    | Inform user (encrypted msgs, gasless).                                               |
| Admin/owner-only silently rejected     | Warn user to verify permissions before calling.                                      |
| "Not confirmed within Ns"              | Tx was sent, may still be processing. Show explorer link. **Never claim it failed.** |
| Domain name where NFT address expected | Explain: need NFT contract address, not domain string.                               |