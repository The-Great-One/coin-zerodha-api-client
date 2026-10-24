from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CoinCredentials:
    user_id: str
    password: str
    totp_key: str


def load_credentials_from_secrets(
    path: str | Path, *, account: str | None = None
) -> CoinCredentials:
    """Load Zerodha credentials from an Auto_Trader-style my_secrets.py file.

    Supports two formats:

    1. **Flat vars** (backward compatible)::

        USER_NAME = "U123"
        PASS = "pw"
        TOTP_KEY = "totp"

    2. **Named accounts** (multi-account)::

        ACCOUNTS = {
            "alice": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
            "bob":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
        }

    When ``ACCOUNTS`` is present, *account* selects the named entry.
    If *account* is ``None``, the first entry in ``ACCOUNTS`` is used
    as the default, or the ``COIN_ZERODHA_ACCOUNT`` environment variable
    is consulted.  When ``ACCOUNTS`` is absent, the flat vars are used
    regardless of *account* (backward compatible).

    Individual values may be overridden with ``AT_KITE_USER_NAME``,
    ``AT_KITE_PASSWORD``, and ``AT_KITE_TOTP_KEY`` environment variables
    (applied per-account when ``ACCOUNTS`` is used, globally otherwise).
    Secrets are never logged or returned as dicts.
    """
    namespace: dict[str, Any] = {}
    secrets_path = Path(path).expanduser().resolve()
    exec(secrets_path.read_text(encoding="utf-8"), namespace)

    accounts: dict[str, dict[str, str]] | None = namespace.get("ACCOUNTS")

    if accounts is not None:
        # --- multi-account mode ---
        if account is None:
            account = os.getenv("COIN_ZERODHA_ACCOUNT")
        if account is None:
            # Default: first key in insertion order (Python 3.7+)
            account = next(iter(accounts))
        if account not in accounts:
            raise KeyError(
                f"Account {account!r} not found in ACCOUNTS. "
                f"Available: {sorted(accounts)}"
            )
        entry = accounts[account]
        return CoinCredentials(
            user_id=os.getenv("AT_KITE_USER_NAME", str(entry["USER_NAME"])),
            password=os.getenv("AT_KITE_PASSWORD", str(entry["PASS"])),
            totp_key=os.getenv("AT_KITE_TOTP_KEY", str(entry["TOTP_KEY"])),
        )

    # --- backward-compatible flat-vars mode ---
    return CoinCredentials(
        user_id=os.getenv("AT_KITE_USER_NAME", str(namespace["USER_NAME"])),
        password=os.getenv("AT_KITE_PASSWORD", str(namespace["PASS"])),
        totp_key=os.getenv("AT_KITE_TOTP_KEY", str(namespace["TOTP_KEY"])),
    )
