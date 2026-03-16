from __future__ import annotations

import typing as t

from fastmcp.exceptions import ToolError

from ton_mcp.core import APP_CTX, AppContext
from ton_mcp.models import DNSRecordItem, DNSRecordsResult, DomainResolveResult
from tonutils.contracts import (
    DNSRecordDNSNextResolver,
    DNSRecordSite,
    DNSRecordStorage,
    DNSRecordWallet,
    TONDNSItem,
)
from tonutils.types import DNSCategory


async def resolve_domain(
    domain: str,
    category: str = "wallet",
    app_ctx: AppContext = APP_CTX,
) -> DomainResolveResult:
    """Resolve a .ton/.t.me domain to its record value.

    Categories: wallet (default), site, storage, dns_next_resolver.
    """
    dns_category = _parse_category(category)

    record = await app_ctx.client.dnsresolve(
        domain=domain,
        category=dns_category,
    )

    value = _format_record(record) if record is not None else None
    return DomainResolveResult(
        domain=domain,
        category=category,
        value=value,
    )


async def get_dns_records(
    dns_item_address: str,
    app_ctx: AppContext = APP_CTX,
) -> DNSRecordsResult:
    """Get all DNS records for a domain.

    Requires the NFT contract address of the domain, not the domain name string.
    """
    dns_item = await TONDNSItem.from_address(
        client=app_ctx.client,
        address=dns_item_address,
    )

    record_items = []
    if dns_item.dns_records:
        for cat, rec in dns_item.dns_records.items():
            record_items.append(DNSRecordItem(
                category=str(cat),
                value=_format_record(rec),
            ))

    return DNSRecordsResult(
        domain=dns_item.domain,
        owner=dns_item.owner_address.to_str(is_bounceable=False),
        records=record_items,
    )


def _parse_category(category: str) -> DNSCategory:
    """Parse DNS category string to enum.

    :param category: Category name.
    :return: DNSCategory enum value.
    :raises ToolError: If category is unknown.
    """
    categories = {
        "wallet": DNSCategory.WALLET,
        "site": DNSCategory.SITE,
        "storage": DNSCategory.STORAGE,
        "dns_next_resolver": DNSCategory.DNS_NEXT_RESOLVER,
    }
    result = categories.get(category.lower())
    if result is None:
        raise ToolError(
            f"Unknown DNS category: '{category}'. "
            f"Available: {', '.join(categories.keys())}."
        )
    return result


def _format_record(
    record: t.Union[
        DNSRecordWallet,
        DNSRecordDNSNextResolver,
        DNSRecordStorage,
        DNSRecordSite,
    ],
) -> str:
    """Format a DNS record value to string.

    :param record: DNS record object.
    :return: Formatted value string.
    """
    if isinstance(record, DNSRecordWallet):
        return record.value.to_str(is_bounceable=False)
    if isinstance(record, DNSRecordDNSNextResolver):
        return record.value.to_str()
    if isinstance(record, DNSRecordStorage):
        return record.value.as_hex.lower()
    if isinstance(record, DNSRecordSite):
        return record.value.as_hex.lower()
    return str(record)
