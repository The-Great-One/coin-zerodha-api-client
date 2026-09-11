from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .client import CoinClient
from .credentials import load_credentials_from_secrets


def default_secrets_path() -> Path:
    """Default Auto_Trader-style secrets path; override with COIN_ZERODHA_SECRETS."""
    configured = os.getenv("COIN_ZERODHA_SECRETS")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Desktop" / "Stocks" / "Auto_Trader" / "my_secrets.py"


def _client(args: argparse.Namespace) -> CoinClient:
    creds = load_credentials_from_secrets(args.secrets, account=args.account)
    c = CoinClient(creds)
    c.login()
    return c


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="coin-zerodha")
    parser.add_argument("--secrets", default=str(default_secrets_path()))
    parser.add_argument(
        "--account", default=None,
        help="Named account from ACCOUNTS dict in secrets file. "
             "Uses COIN_ZERODHA_ACCOUNT env var if set, otherwise first entry.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profile")
    sub.add_parser("holdings")
    sub.add_parser("sips")
    sub.add_parser("swp")
    sub.add_parser("stp")
    sub.add_parser("flows", help="Active SIP + SWP + STP in one view (what is this account actually running?)")
    orders = sub.add_parser("orders")
    orders.add_argument("--from-date")
    orders.add_argument("--to-date")
    args = parser.parse_args(argv)

    client = _client(args)
    if args.command == "profile":
        _print_json(client.profile())
    elif args.command == "holdings":
        _print_json(client.holdings())
    elif args.command == "sips":
        _print_json(client.sips())
    elif args.command == "swp":
        _print_json(client.swp())
    elif args.command == "stp":
        _print_json(client.stp())
    elif args.command == "flows":
        _print_json(_flows(client))
    elif args.command == "orders":
        _print_json(client.orders(from_date=args.from_date, to_date=args.to_date))
    return 0


def _rows(payload: Any, *keys: str) -> list[dict[str, Any]]:
    """Coin returns either a bare list or {'data': [...]} / {key: [...]}."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for k in keys:
            v = payload.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
        for v in payload.values():
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
    return []


def _flows(client: CoinClient) -> dict[str, Any]:
    """Aggregate active SIP/SWP/STP into one summary."""
    out: dict[str, Any] = {}
    for label, fn in (("sips", client.sips), ("swp", client.swp), ("stp", client.stp)):
        try:
            out[label] = _rows(fn(), label)
        except Exception as e:  # fail-soft: a closed/absent product must not kill the view
            out[label] = []
            out[f"{label}_error"] = f"{type(e).__name__}: {e}"
    return out


if __name__ == "__main__":
    raise SystemExit(main())
