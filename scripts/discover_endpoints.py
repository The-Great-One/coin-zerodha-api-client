#!/usr/bin/env python3
"""Discover Coin API paths from the current frontend bundle.

This is intentionally read-only and does not require auth.
"""
from __future__ import annotations

import re
import requests

HOME = "https://coin.zerodha.com/"


def main() -> int:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    home = session.get(HOME, timeout=20)
    home.raise_for_status()
    assets = sorted(set(re.findall(r'(?:src|href)=["\']([^"\']+\.js[^"\']*)', home.text)))
    paths: set[str] = set()
    for asset in assets:
        url = asset if asset.startswith("http") else HOME.rstrip("/") + asset
        js = session.get(url, timeout=20)
        js.raise_for_status()
        paths.update(re.findall(r'"(/api/[^"]+)"', js.text))
        paths.update(re.findall(r"'(/api/[^']+)'", js.text))
    for path in sorted(paths):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
