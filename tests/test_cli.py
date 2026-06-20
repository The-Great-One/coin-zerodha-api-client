from pathlib import Path

from coin_zerodha.cli import default_secrets_path


def test_default_secrets_path_is_home_relative_and_not_user_absolute(monkeypatch):
    monkeypatch.delenv("COIN_ZERODHA_SECRETS", raising=False)
    path = default_secrets_path()

    assert path == Path.home() / "Desktop" / "Stocks" / "Auto_Trader" / "my_secrets.py"
    assert "/Users/sahilgoel" not in Path("src/coin_zerodha/cli.py").read_text()


def test_default_secrets_path_can_be_overridden_by_env(monkeypatch):
    monkeypatch.setenv("COIN_ZERODHA_SECRETS", "~/secure/my_secrets.py")

    assert default_secrets_path() == Path("~/secure/my_secrets.py").expanduser()


def test_cli_account_flag_passed_to_credentials_loader(tmp_path, monkeypatch, capsys):
    """--account flag selects the named account from ACCOUNTS dict."""
    from coin_zerodha import cli
    from coin_zerodha.client import CoinClient

    secrets = tmp_path / "my_secrets.py"
    secrets.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")

    captured_creds = []

    def fake_init(self, credentials, *, session=None, timeout=20.0):
        captured_creds.append(credentials)

    monkeypatch.setattr(CoinClient, "__init__", fake_init)
    monkeypatch.setattr(CoinClient, "login", lambda self: None)
    monkeypatch.setattr(CoinClient, "profile", lambda self: {"name": "test"})

    exit_code = cli.main(["--secrets", str(secrets), "--account", "dad", "profile"])
    assert exit_code == 0
    assert len(captured_creds) == 1
    assert captured_creds[0].user_id == "U2"


def test_cli_no_account_flag_uses_default(tmp_path, monkeypatch, capsys):
    """Without --account, the first ACCOUNTS entry is used."""
    from coin_zerodha import cli
    from coin_zerodha.client import CoinClient

    secrets = tmp_path / "my_secrets.py"
    secrets.write_text("""
ACCOUNTS = {
    "sahil": {"USER_NAME": "U1", "PASS": "pw1", "TOTP_KEY": "t1"},
    "dad":   {"USER_NAME": "U2", "PASS": "pw2", "TOTP_KEY": "t2"},
}
""")

    captured_creds = []

    def fake_init(self, credentials, *, session=None, timeout=20.0):
        captured_creds.append(credentials)

    monkeypatch.setattr(CoinClient, "__init__", fake_init)
    monkeypatch.setattr(CoinClient, "login", lambda self: None)
    monkeypatch.setattr(CoinClient, "profile", lambda self: {"name": "test"})

    exit_code = cli.main(["--secrets", str(secrets), "profile"])
    assert exit_code == 0
    assert len(captured_creds) == 1
    assert captured_creds[0].user_id == "U1"  # first entry is default
