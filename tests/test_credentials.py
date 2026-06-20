from pathlib import Path

from coin_zerodha.credentials import load_credentials_from_secrets


def test_load_credentials_from_auto_trader_style_secrets(tmp_path: Path):
    p = tmp_path / "my_secrets.py"
    p.write_text("USER_NAME='U123'\nPASS='pw'\nTOTP_KEY='totp'\nAPI_KEY='ignored'\n")

    creds = load_credentials_from_secrets(p)

    assert creds.user_id == "U123"
    assert creds.password == "pw"
    assert creds.totp_key == "totp"


def test_load_credentials_from_flat_vars_still_works(tmp_path: Path):
    """Backward compat: flat USER_NAME/PASS/TOTP_KEY still load."""
    p = tmp_path / "my_secrets.py"
    p.write_text("USER_NAME='U123'\nPASS='pw'\nTOTP_KEY='totp'\n")
    creds = load_credentials_from_secrets(p)
    assert creds.user_id == "U123"
    assert creds.password == "pw"
    assert creds.totp_key == "totp"


def test_load_credentials_from_accounts_dict(tmp_path: Path):
    """Multi-account: ACCOUNTS dict with named entries."""
    p = tmp_path / "my_secrets.py"
    p.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")
    creds = load_credentials_from_secrets(p, account="sahil")
    assert creds.user_id == "U1"
    assert creds.password == "pw1"
    assert creds.totp_key == "t1"

    creds2 = load_credentials_from_secrets(p, account="dad")
    assert creds2.user_id == "U2"


def test_load_credentials_default_account_from_dict(tmp_path: Path):
    """When ACCOUNTS exists but no account specified, use first entry as default."""
    p = tmp_path / "my_secrets.py"
    p.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")
    creds = load_credentials_from_secrets(p)  # no account specified
    assert creds.user_id == "U1"  # first entry is default


def test_load_credentials_env_var_overrides_account(monkeypatch, tmp_path: Path):
    """COIN_ZERODHA_ACCOUNT env var picks the account."""
    monkeypatch.setenv("COIN_ZERODHA_ACCOUNT", "dad")
    p = tmp_path / "my_secrets.py"
    p.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")
    creds = load_credentials_from_secrets(p)
    assert creds.user_id == "U2"


def test_load_credentials_missing_account_raises(tmp_path: Path):
    """Requesting a non-existent account raises KeyError with helpful message."""
    p = tmp_path / "my_secrets.py"
    p.write_text("""
ACCOUNTS = {"sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"}}
""")
    import pytest
    with pytest.raises(KeyError, match="Account 'nobody' not found"):
        load_credentials_from_secrets(p, account="nobody")


def test_load_credentials_env_var_overrides_explicit_account(monkeypatch, tmp_path: Path):
    """Explicit account= parameter takes precedence over env var."""
    monkeypatch.setenv("COIN_ZERODHA_ACCOUNT", "dad")
    p = tmp_path / "my_secrets.py"
    p.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")
    creds = load_credentials_from_secrets(p, account="sahil")
    assert creds.user_id == "U1"  # explicit wins over env
