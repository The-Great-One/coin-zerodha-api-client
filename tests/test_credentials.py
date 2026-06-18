from pathlib import Path

from coin_zerodha.credentials import load_credentials_from_secrets


def test_load_credentials_from_auto_trader_style_secrets(tmp_path: Path):
    p = tmp_path / "my_secrets.py"
    p.write_text("USER_NAME='U123'\nPASS='pw'\nTOTP_KEY='totp'\nAPI_KEY='ignored'\n")

    creds = load_credentials_from_secrets(p)

    assert creds.user_id == "U123"
    assert creds.password == "pw"
    assert creds.totp_key == "totp"
