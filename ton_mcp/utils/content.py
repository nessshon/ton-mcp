from __future__ import annotations

import typing as t

import aiohttp
from pytoniq_core import Cell
from tonutils.clients.protocol import ClientProtocol
from ton_mcp.utils.getters import (
    get_nft_address_by_index,
    get_nft_content,
    get_nft_data,
)
from tonutils.contracts.nft.tlb import (
    OffchainContent,
    OnchainContent,
)
from tonutils.types import MetadataPrefix

_FETCH_TIMEOUT: t.Final[float] = 5.0
_IPFS_FETCH_TIMEOUT: t.Final[float] = 10.0
_IPFS_GATEWAY: t.Final[str] = "https://ipfs.io/ipfs/"


async def parse_metadata(
    cell: Cell,
) -> t.Tuple[t.Dict[str, t.Any], t.Optional[str]]:
    """Parse a TEP-64 content Cell and resolve metadata.

    Handles on-chain, off-chain, and semi-chain formats.
    Fetches JSON from URI when applicable.

    :param cell: Raw content Cell from a get-method.
    :return: Tuple of (metadata dict, optional hint on failure).
    """
    content = _parse_content_cell(cell)
    return await _resolve_content_object(content)


async def parse_collection_content(
    cell: Cell,
) -> t.Tuple[t.Dict[str, t.Any], t.Optional[str], t.Optional[str]]:
    """Parse an NFT collection content Cell from ``get_collection_data``.

    The get-method returns a TEP-64 content Cell (prefix 0x00/0x01)
    with the collection metadata only.

    :param cell: Collection content Cell from ``get_collection_data``.
    :return: Tuple of (collection metadata dict, content URI if off-chain,
        optional hint on failure).
    """
    content = _parse_content_cell(cell)
    content_uri: t.Optional[str] = None
    if isinstance(content, OffchainContent):
        content_uri = content.uri
    metadata, hint = await _resolve_content_object(content)
    return metadata, content_uri, hint


async def resolve_items_prefix_uri(
    client: ClientProtocol,
    collection_address: t.Any,
) -> t.Optional[str]:
    """Derive the items prefix URI from the first minted NFT.

    Calls ``get_nft_address_by_index(0)`` to find the first item,
    reads its individual content (suffix), then calls
    ``get_nft_content(0, individual_content)`` to get the full URI.
    The prefix is the full URI with the suffix stripped.

    :param client: TON client instance.
    :param collection_address: Collection contract address.
    :return: Items prefix URI, or ``None`` on failure.
    """
    try:
        nft_address = await get_nft_address_by_index(
            client=client,
            address=collection_address,
            index=0,
        )
        nft_data = await get_nft_data(
            client=client,
            address=nft_address,
        )
        individual_content: Cell = nft_data[4]

        suffix_cs = individual_content.begin_parse()
        suffix = suffix_cs.load_snake_string()

        full_cell = await get_nft_content(
            client=client,
            address=collection_address,
            index=0,
            individual_nft_content=individual_content,
        )
        full_content = _parse_content_cell(full_cell)
        if not isinstance(full_content, OffchainContent):
            return None

        full_uri = full_content.uri
        if suffix and full_uri.endswith(suffix):
            return full_uri[: -len(suffix)]
        return full_uri
    except (Exception,):
        return None


async def resolve_nft_item_content(
    client: ClientProtocol,
    collection_address: t.Any,
    index: int,
    individual_content: Cell,
) -> t.Tuple[t.Dict[str, t.Any], t.Optional[str]]:
    """Resolve full NFT item metadata via the collection's get-method.

    Calls ``get_nft_content`` on the collection contract to combine
    the collection prefix URI with the item suffix URI, then fetches
    the resulting JSON metadata.

    Falls back to parsing individual content directly on failure.

    :param client: TON client instance.
    :param collection_address: Collection contract address.
    :param index: Item index in the collection.
    :param individual_content: Raw content Cell from ``get_nft_data``.
    :return: Tuple of (metadata dict, optional hint on failure).
    """
    try:
        full_cell = await get_nft_content(
            client=client,
            address=collection_address,
            index=index,
            individual_nft_content=individual_content,
        )
        return await parse_metadata(full_cell)
    except (Exception,):
        pass

    try:
        return await parse_metadata(individual_content)
    except (Exception,):
        pass

    try:
        cs = individual_content.begin_parse()
        suffix = cs.load_snake_string()
        return (
            {"suffix_uri": suffix},
            "Could not resolve full item URI; showing raw suffix only",
        )
    except (Exception,):
        return {}, "Failed to parse NFT item content"


def _normalize_uri(uri: str) -> str:
    """Convert IPFS URI to HTTP gateway URL.

    :param uri: Original URI (http, https, or ipfs scheme).
    :return: HTTP-accessible URL.
    """
    if uri.startswith("ipfs://"):
        return _IPFS_GATEWAY + uri[7:]
    return uri


def _is_ipfs_uri(uri: str) -> bool:
    """Check whether a URI points to IPFS content.

    :param uri: URI to check.
    :return: True if IPFS-related.
    """
    return uri.startswith("ipfs://") or "/ipfs/" in uri


async def _fetch_json(uri: str) -> t.Dict[str, t.Any]:
    """Fetch and parse JSON metadata from a URI.

    Uses a longer timeout for IPFS gateways.

    :param uri: Metadata URI (http/https/ipfs).
    :return: Parsed JSON as dict.
    :raises aiohttp.ClientError: On network failure.
    :raises aiohttp.ClientResponseError: On non-2xx status.
    """
    url = _normalize_uri(uri)
    timeout_val = _IPFS_FETCH_TIMEOUT if _is_ipfs_uri(uri) else _FETCH_TIMEOUT
    timeout = aiohttp.ClientTimeout(total=timeout_val)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data).__name__}")
            return data


def _parse_content_cell(
    cell: Cell,
) -> t.Union[OnchainContent, OffchainContent]:
    """Parse a TEP-64 content Cell into a typed content object.

    Reads the prefix byte to determine the format:
    - ``0x00``: on-chain metadata (HashMap with SHA-256 keys).
    - ``0x01``: off-chain metadata (URI as snake string).

    :param cell: Raw content Cell from a get-method.
    :return: Parsed OnchainContent or OffchainContent.
    :raises ValueError: If the prefix byte is invalid.
    """
    cs = cell.begin_parse()
    prefix = MetadataPrefix(cs.load_uint(8))

    if prefix == MetadataPrefix.ONCHAIN:
        return OnchainContent.deserialize(cs, with_prefix=False)
    return OffchainContent.deserialize(cs, with_prefix=False)


def _extract_onchain_fields(content: OnchainContent) -> t.Dict[str, str]:
    """Extract string fields from on-chain metadata.

    Filters out unknown integer keys and unparsed Cell values.

    :param content: Parsed OnchainContent.
    :return: Dict of field name to string value.
    """
    return {
        k: v
        for k, v in content.metadata.items()
        if isinstance(k, str) and isinstance(v, str)
    }


async def _resolve_content_object(
    content: t.Union[OnchainContent, OffchainContent],
) -> t.Tuple[t.Dict[str, t.Any], t.Optional[str]]:
    """Resolve a parsed content object into a metadata dict.

    For off-chain content, fetches JSON from the URI.
    For on-chain content with a ``uri`` key (semi-chain), fetches JSON
    and merges with on-chain fields (on-chain takes priority).

    :param content: Parsed TEP-64 content object.
    :return: Tuple of (metadata dict, optional hint on failure).
    """
    if isinstance(content, OffchainContent):
        try:
            data = await _fetch_json(content.uri)
            return data, None
        except (Exception,):
            return (
                {"uri": content.uri},
                f"Failed to fetch metadata from {content.uri}",
            )

    fields = _extract_onchain_fields(content)
    uri = fields.get("uri")

    if uri:
        try:
            offchain = await _fetch_json(uri)
            return {**offchain, **fields}, None
        except (Exception,):
            return fields, f"Failed to fetch off-chain metadata from {uri}"

    return fields, None
