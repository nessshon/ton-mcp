from __future__ import annotations

import asyncio
import base64
import typing as t
from urllib.parse import quote

import aiohttp
from tonutils.types import NetworkGlobalID

_QR_SERVICE_URL = "https://qrcode.ness.su/create"
_QR_IMAGE_URL = "https://avatars.githubusercontent.com/u/131016009"

_SHORTEN_TIMEOUT: float = 5.0

_GET_SHORTENERS: t.Final[t.List[str]] = [
    "https://is.gd/create.php?format=json&url=",
    "https://v.gd/create.php?format=json&url=",
]
_POST_SHORTENER: t.Final[str] = "https://link.ness.su/shorten"

_NETWORK_PREFIXES: t.Final[t.Dict[NetworkGlobalID, str]] = {
    NetworkGlobalID.MAINNET: "",
    NetworkGlobalID.TESTNET: "testnet.",
    NetworkGlobalID.TETRA: "tetra.",
}


def explorer_url(
    network: NetworkGlobalID,
    tx_hash: str,
    explorer: str,
) -> str:
    """Build transaction explorer URL.

    :param network: Current network.
    :param tx_hash: Transaction hash.
    :param explorer: Explorer name: ``tonviewer`` or ``tonscan``.
    :return: Explorer URL for the transaction.
    """
    prefix = _NETWORK_PREFIXES.get(network, "")

    if explorer == "tonscan":
        return f"https://{prefix}tonscan.org/tx/{tx_hash}"

    return f"https://{prefix}tonviewer.com/transaction/{tx_hash}"


async def shorten_urls(urls: t.List[str]) -> t.List[str]:
    """Shorten URLs via is.gd, v.gd, or link.ness.su as fallback.

    :param urls: URLs to shorten.
    :return: Shortened URLs (originals on failure).
    """
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=_SHORTEN_TIMEOUT),
    ) as session:
        return list(await asyncio.gather(*[_shorten_one(session, u) for u in urls]))


async def _shorten_one(session: aiohttp.ClientSession, url: str) -> str:
    """Try each shortener service, return original on failure.

    Order: is.gd -> v.gd -> link.ness.su.

    :param session: HTTP session.
    :param url: URL to shorten.
    :return: Shortened URL or original.
    """
    encoded = quote(url, safe="")
    for service in _GET_SHORTENERS:
        try:
            async with session.get(f"{service}{encoded}") as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if "shorturl" in data:
                        return data["shorturl"]
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError):
            continue

    try:
        async with session.post(
            _POST_SHORTENER,
            json={"url": url},
        ) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                if "short_url" in data:
                    return data["short_url"]
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError):
        pass

    return url


def make_qr_url(connect_url: str) -> str:
    """Build QR code image URL.

    :param connect_url: TON Connect URL to encode.
    :return: QR code image URL.
    """
    data_b64 = base64.b64encode(connect_url.encode()).decode()
    image_b64 = base64.b64encode(_QR_IMAGE_URL.encode()).decode()
    return (
        f"{_QR_SERVICE_URL}?"
        f"box_size=20&border=7&image_padding=20"
        f"&data={data_b64}&image_url={image_b64}"
    )
