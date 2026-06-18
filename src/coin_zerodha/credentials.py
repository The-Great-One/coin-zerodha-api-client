from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Any


@dataclass(frozen=True)
class CoinCredentials:
    user_id: str
    password: str
    totp_key: str


def load_credentials_from_secrets(path: str | Path) -> CoinCredentials:
    """Load Zerodha credentials from an Auto_Trader-style my_secrets.py file.

    Values may be overridden with AT_KITE_USER_NAME, AT_KITE_PASSWORD,
    and AT_KITE_TOTP_KEY. Secrets are never logged or returned as dicts.
    """

    namespace: dict[str, Any] = {}
    secrets_path = Path(path).expanduser().resolve()
    exec(secrets_path.read_text(encoding="utf-8"), namespace)
    return CoinCredentials(
        user_id=os.getenv("AT_KITE_USER_NAME", str(namespace["USER_NAME"])),
        password=os.getenv("AT_KITE_PASSWORD", str(namespace["PASS"])),
        totp_key=os.getenv("AT_KITE_TOTP_KEY", str(namespace["TOTP_KEY"])),
    )
