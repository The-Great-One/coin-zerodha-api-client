"""Scrape underlying fund holdings from investing.com.

Investing.com publishes mutual fund holdings pages that list each stock's
name, ISIN, weight, price, and daily change.  This module provides a
standalone scraper (no Coin auth required — the fund pages are public).

Usage::

    from coin_zerodha.investing import InvestingFundHoldings

    holdings = InvestingFundHoldings.fetch("franklin-us-opportunities-fund-a")
    for h in holdings:
        print(h["name"], h["weight"])

    # Search for a fund if you don't know the URL slug:
    results = InvestingFundHoldings.search("jennison global equity")
    for slug, name in results:
        print(slug, name)

    # Prefer Indian investing.com (in.investing.com):
    holdings = InvestingFundHoldings.fetch("franklin-us-opportunities-fund-i-au", region="in")
"""

from __future__ import annotations

import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_BASE_URLS = {
    "global": "https://www.investing.com",
    "in": "https://in.investing.com",
}

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)


def _fetch(url: str, *, timeout: float = 20, referer: str = "") -> str:
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class _FundHolding:
    name: str
    isin: str = ""
    weight: float = 0.0
    price: str = ""
    change_pct: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "isin": self.isin,
            "weight": self.weight,
            "price": self.price,
            "change_pct": self.change_pct,
        }


@dataclass
class _FundSector:
    sector: str
    weight: float = 0.0
    benchmark: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector": self.sector,
            "weight": self.weight,
            "benchmark": self.benchmark,
        }


@dataclass
class _FundResult:
    url: str
    name: str = ""
    holdings: list[_FundHolding] = field(default_factory=list)
    sectors: list[_FundSector] = field(default_factory=list)
    asset_allocation: list[dict[str, Any]] = field(default_factory=list)
    title: str = ""
    isin: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name or self.title,
            "url": self.url,
            "title": self.title,
            "isin": self.isin,
            "holdings": [h.to_dict() for h in self.holdings],
            "sectors": [s.to_dict() for s in self.sectors],
            "asset_allocation": self.asset_allocation,
        }


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------

_SECTOR_NAMES: frozenset[str] = frozenset(
    {
        "financial services",
        "technology",
        "industrials",
        "healthcare",
        "consumer cyclical",
        "consumer defensive",
        "energy",
        "utilities",
        "basic materials",
        "real estate",
        "communication services",
    }
)

_EXCLUDE_NAMES: frozenset[str] = frozenset(
    {
        "p/e ratio",
        "price to book",
        "price to sales",
        "price to cash flow",
        "dividend yield",
        "5 years earnings growth",
        "preferred",
        "other",
        "cash",
        "shares",
        "stocks",
        "bonds",
        "large",
        "mid",
        "small",
        "value",
        "blend",
        "growth",
    }
)


def _text(el: str) -> str:
    """Strip HTML tags and normalise whitespace from an HTML element."""
    return re.sub(r"<[^>]+>", "", el).strip()


def _is_stock_name(name: str) -> bool:
    """Return False for rows that are metrics, sectors, or non-stock entries."""
    lower = name.lower()
    if lower in _EXCLUDE_NAMES or lower in _SECTOR_NAMES:
        return False
    if any(x in lower for x in ["treasury", "bond", "note", "united states treasury"]):
        return False
    # ISIN-only row (12-character alphanumeric)
    if re.fullmatch(r"[A-Z0-9]{12}", name):
        return False
    return True


def _parse_row(cells: list[str]) -> _FundHolding | None:
    """Try to parse a table row as a fund holding.

    Two common formats on investing.com:
    1) Name | ISIN  | weight | price | change%   (EU/global funds)
    2) Name |  -    | weight | price | change%   (US funds)
    """
    if len(cells) < 3:
        return None

    name = cells[0]
    if not _is_stock_name(name):
        return None

    # Attempt to find the weight column — it is always a float < 100.
    weight: float | None = None
    weight_idx: int | None = None
    for i, cell in enumerate(cells[1:], start=1):
        try:
            w = float(cell)
        except ValueError:
            continue
        if 0 < w < 100:
            weight = w
            weight_idx = i
            break

    if weight is None or weight_idx is None:
        return None

    # ISIN detection: the cell before weight may be an ISIN (12-char alphanumeric).
    isin = ""
    if weight_idx >= 2 and re.fullmatch(r"[A-Z0-9]{12}", cells[weight_idx - 1]):
        isin = cells[weight_idx - 1]

    price = cells[weight_idx + 1] if len(cells) > weight_idx + 1 else ""
    change = cells[weight_idx + 2] if len(cells) > weight_idx + 2 else ""

    return _FundHolding(name=name, isin=isin, weight=weight, price=price, change_pct=change)


def _parse_sector_row(cells: list[str]) -> _FundSector | None:
    """Parse a sector row (Name | current% | benchmark%)."""
    if len(cells) < 3:
        return None
    name = cells[0].lower()
    if name not in _SECTOR_NAMES:
        return None
    try:
        weight = float(cells[1])
        bench = float(cells[2])
    except ValueError:
        return None
    return _FundSector(sector=cells[0], weight=weight, benchmark=bench)


def _parse_asset_allocation_row(cells: list[str]) -> dict[str, Any] | None:
    """Parse an asset allocation row like Cash | 0.97 | 1.01 | 0.04."""
    if len(cells) < 4:
        return None
    name = cells[0].lower()
    if name not in {"cash", "shares", "stocks", "bonds", "preferred", "other"}:
        return None
    try:
        current = float(cells[1])
        benchmark = float(cells[2])
        diff = float(cells[3]) if len(cells) > 3 else 0.0
    except ValueError:
        return None
    return {"type": name, "current": current, "benchmark": benchmark, "diff": diff}


def _extract(body: str) -> _FundResult:
    """Extract holdings, sectors and metadata from an investing.com holdings page."""
    tables = re.findall(r"<table[^>]*>(.*?)</table>", body, re.DOTALL)

    result = _FundResult(url="")

    # Title
    title_m = re.search(r"<title>(.*?)</title>", body)
    if title_m:
        result.title = title_m.group(1).strip()

    for table in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL)
        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            clean = [_text(c) for c in cells if _text(c) and _text(c) != "&nbsp;"]

            if not clean:
                continue

            # Try holding
            holding = _parse_row(clean)
            if holding:
                result.holdings.append(holding)
                continue

            # Try sector
            sector = _parse_sector_row(clean)
            if sector:
                result.sectors.append(sector)
                continue

            # Try asset allocation
            alloc = _parse_asset_allocation_row(clean)
            if alloc:
                result.asset_allocation.append(alloc)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class InvestingFundHoldings:
    """Scrape underlying offshore mutual fund holdings from investing.com.

    No API key required — fund pages are public.  Supports both global
    (www.investing.com) and Indian (in.investing.com) variants.
    """

    @staticmethod
    def fetch(slug: str, *, region: str = "global", timeout: float = 20) -> dict[str, Any]:
        """Fetch holdings for a fund by its URL slug.

        Args:
            slug: The fund page slug, e.g. ``"franklin-us-opportunities-fund-a"``
                  or ``"jpmorgan-euro-dynamicfund-d-acc-eur"``.
            region: ``"global"`` for www.investing.com, ``"in"`` for in.investing.com.

        Returns:
            A dict with ``holdings``, ``sectors``, ``asset_allocation``, ``name``,
            ``url``, and ``title``.

        Raises:
            urllib.error.HTTPError: If the page returns 404.
        """
        base = _BASE_URLS[region]
        holdings_url = f"{base}/funds/{slug}-holdings"
        body = _fetch(holdings_url, timeout=timeout, referer=f"{base}/funds/{slug}")
        result = _extract(body)
        result.url = holdings_url
        return result.to_dict()

    @staticmethod
    def search(query: str, *, region: str = "global", timeout: float = 20) -> list[tuple[str, str]]:
        """Search investing.com for a fund and return matching slugs.

        Args:
            query: Search term, e.g. ``"jennison global equity"`` or ``"PIPGX"``.
            region: ``"global"`` or ``"in"``.

        Returns:
            List of ``(slug, display_name)`` tuples.  The slug can be passed
            directly to :meth:`fetch`.
        """
        base = _BASE_URLS[region]
        search_url = f"{base}/search/?q={urllib.parse.quote(query)}"
        body = _fetch(search_url, timeout=timeout, referer=base + "/")

        # Extract fund links from search results
        slugs_seen: set[str] = set()
        results: list[tuple[str, str]] = []

        # Find all fund links near their display text
        for m in re.finditer(r'href="(/funds/([a-z0-9\-]+))"[^>]*>(.*?)</a>', body, re.DOTALL):
            if m is None:
                continue
            slug = m.group(2)
            # Extract display text — remove nested tags
            text = re.sub(r"<[^>]+>", "", m.group(3) or "").strip()
            # Filter out generic links
            if slug in slugs_seen:
                continue
            if slug in ("", "major-funds", "world-funds", "best-funds"):
                continue
            if any(x in slug for x in ("vanguard", "pimco", "american-funds", "scotia", "prudential-jennison-equity-income")):
                continue
            slugs_seen.add(slug)
            results.append((slug, text))

        return results

    @staticmethod
    def batch_fetch(
        slugs_and_names: list[tuple[str, str]],
        *,
        region: str = "global",
        timeout: float = 20,
        delay: float = 2.0,
    ) -> dict[str, dict[str, Any]]:
        """Fetch holdings for multiple funds.

        Args:
            slugs_and_names: List of ``(slug, display_name)`` tuples.
            region: ``"global"`` or ``"in"``.
            timeout: Per-request timeout.
            delay: Seconds to sleep between requests.

        Returns:
            Dict keyed by display name, values are the dicts from :meth:`fetch`.
        """
        results: dict[str, dict[str, Any]] = {}
        for slug, name in slugs_and_names:
            try:
                data = InvestingFundHoldings.fetch(slug, region=region, timeout=timeout)
                results[name] = data
            except Exception as exc:
                results[name] = {"error": str(exc), "slug": slug, "holdings": [], "sectors": []}
            time.sleep(delay)
        return results
