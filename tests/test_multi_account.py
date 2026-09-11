"""Multi-account support tests for coin_zerodha.credentials."""
from __future__ import annotations

import pytest

from coin_zerodha.credentials import load_credentials_from_secrets

MULTI = """
ACCOUNTS = {
    "alpha": {"USER_NAME": "AAA111", "PASS": "pa", "TOTP_KEY": "KA"},
    "beta": {"USER_NAME": "BBB222", "PASS": "pb", "TOTP_KEY": "KB"},
}
"""

FLAT = """
USER_NAME = "FLAT1"
PASS = "pf"
TOTP_KEY = "KF"
"""


@pytest.fixture
def multi_file(tmp_path):
    p = tmp_path / "multi.py"
    p.write_text(MULTI)
    return p


@pytest.fixture
def flat_file(tmp_path):
    p = tmp_path / "flat.py"
    p.write_text(FLAT)
    return p


def test_named_account_selects_correct_entry(multi_file):
    a = load_credentials_from_secrets(multi_file, account="alpha")
    b = load_credentials_from_secrets(multi_file, account="beta")
    assert a.user_id == "AAA111"
    assert b.user_id == "BBB222"
    # isolation: selecting one account must not leak the other's secrets
    assert a.password != b.password
    assert a.totp_key != b.totp_key


def test_default_account_is_first_entry(multi_file):
    assert load_credentials_from_secrets(multi_file).user_id == "AAA111"


def test_env_var_selects_account(multi_file, monkeypatch):
    monkeypatch.setenv("COIN_ZERODHA_ACCOUNT", "beta")
    assert load_credentials_from_secrets(multi_file).user_id == "BBB222"


def test_explicit_account_beats_env(multi_file, monkeypatch):
    monkeypatch.setenv("COIN_ZERODHA_ACCOUNT", "beta")
    assert load_credentials_from_secrets(multi_file, account="alpha").user_id == "AAA111"


def test_unknown_account_raises_keyerror(multi_file):
    with pytest.raises(KeyError) as exc:
        load_credentials_from_secrets(multi_file, account="ghost")
    assert "ghost" in str(exc.value)
    # the error must list what IS available so the operator can fix it
    assert "alpha" in str(exc.value)


def test_flat_format_still_works(flat_file):
    c = load_credentials_from_secrets(flat_file)
    assert c.user_id == "FLAT1"
    assert c.password == "pf"


def test_flat_format_ignores_account_arg(flat_file):
    """Backward compat: passing account to a flat file must not error."""
    assert load_credentials_from_secrets(flat_file, account="whatever").user_id == "FLAT1"


def test_env_overrides_values(multi_file, monkeypatch):
    monkeypatch.setenv("AT_KITE_USER_NAME", "ENVUSER")
    assert load_credentials_from_secrets(multi_file, account="alpha").user_id == "ENVUSER"
