# coin-zerodha-api-client

Unofficial, read-first Python client for Coin by Zerodha's web APIs.

## Auth

Coin reuses a Kite web login session. The client:

1. Logs into `https://kite.zerodha.com/api/login` with user id/password.
2. Submits TOTP to `https://kite.zerodha.com/api/twofa`.
3. Visits `https://coin.zerodha.com/login`, which establishes `coin_session`.
4. Uses the `public_token` cookie as the `X-CSRFToken` header for `/api/...` requests.

Credentials can be loaded from the existing Auto_Trader `my_secrets.py` file. By default the CLI reads `~/Desktop/Stocks/Auto_Trader/my_secrets.py`; override with `--secrets` or `COIN_ZERODHA_SECRETS`.

```bash
python -m coin_zerodha.cli profile
python -m coin_zerodha.cli holdings --secrets ~/Desktop/Stocks/Auto_Trader/my_secrets.py
COIN_ZERODHA_SECRETS=~/secure/my_secrets.py python -m coin_zerodha.cli sips
```

### Multi-Account Support

To manage multiple Zerodha accounts (e.g., personal and family), define an
`ACCOUNTS` dict in your secrets file:

```python
# my_secrets.py
ACCOUNTS = {
    "alice": {
        "USER_NAME": "U123",
        "PASS": "your-password",
        "TOTP_KEY": "your-totp-secret",
    },
    "bob": {
        "USER_NAME": "U456",
        "PASS": "his-password",
        "TOTP_KEY": "his-totp-secret",
    },
}
```

Then select the account via CLI:

```bash
coin-zerodha --account alice holdings
coin-zerodha --account bob profile
```

Or set the `COIN_ZERODHA_ACCOUNT` environment variable:

```bash
export COIN_ZERODHA_ACCOUNT=dad
coin-zerodha holdings  # uses "bob" account
```

The old flat-vars format (`USER_NAME`, `PASS`, `TOTP_KEY` at module level)
continues to work and is treated as the default account.

## Safety

Unit tests mock HTTP; they do not hit Zerodha or print secrets. Mutating endpoints exist behind explicit methods only; the initial CLI exposes read-only smoke commands.
