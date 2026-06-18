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
