# coin-zerodha-api-client

Unofficial, read-first Python client for Coin by Zerodha's web APIs.

## Auth

Coin reuses a Kite web login session. The client:

1. Logs into `https://kite.zerodha.com/api/login` with user id/password.
2. Submits TOTP to `https://kite.zerodha.com/api/twofa`.
3. Visits `https://coin.zerodha.com/login`, which establishes `coin_session`.
4. Uses the `public_token` cookie as the `X-CSRFToken` header for `/api/...` requests.

Credentials can be loaded from the existing Auto_Trader `my_secrets.py` file.

```bash
python -m coin_zerodha.cli profile --secrets /Users/sahilgoel/Desktop/Stocks/Auto_Trader/my_secrets.py
python -m coin_zerodha.cli holdings --secrets /Users/sahilgoel/Desktop/Stocks/Auto_Trader/my_secrets.py
```

## Safety

Unit tests mock HTTP; they do not hit Zerodha or print secrets. Mutating endpoints exist behind explicit methods only; the initial CLI exposes read-only smoke commands.
