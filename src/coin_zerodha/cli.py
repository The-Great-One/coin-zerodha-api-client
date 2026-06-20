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
    elif args.command == "orders":
        _print_json(client.orders(from_date=args.from_date, to_date=args.to_date))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
