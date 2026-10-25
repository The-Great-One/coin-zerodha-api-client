<div align="center">

<img src="https://via.placeholder.com/120x120.png?text=CZ" alt="coin-zerodha-api-client logo" width="120" height="120" />

# coin-zerodha-api-client

**Unofficial Python client for Coin by Zerodha's web APIs.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/The-Great-One/coin-zerodha-api-client)](https://github.com/The-Great-One/coin-zerodha-api-client/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/The-Great-One/coin-zerodha-api-client)](https://github.com/The-Great-One/coin-zerodha-api-client/pulls)
[![GitHub stars](https://img.shields.io/github/stars/The-Great-One/coin-zerodha-api-client?style=social)](https://github.com/The-Great-One/coin-zerodha-api-client/stargazers)

[Report Bug](https://github.com/The-Great-One/coin-zerodha-api-client/issues/new?template=bug_report.md) · [Request Feature](https://github.com/The-Great-One/coin-zerodha-api-client/issues/new?template=feature_request.md)

</div>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## About

`coin-zerodha-api-client` is an unofficial, read-first Python client for Coin by
Zerodha's web APIs. Coin reuses a Kite web login session (no OAuth app needed).

## Features

- ✅ Reuses a Kite web login session to access Coin by Zerodha
- ✅ Read-only smoke commands: `profile`, `holdings`, `sips`
- ✅ Multi-account support via an `ACCOUNTS` dict in your secrets file
- ✅ Per-account credential overrides via `AT_KITE_*` env vars
- ✅ Secrets are never logged or returned as dicts
- ✅ Unit tests mock HTTP (no live calls, no secrets printed)
- 🚧 Mutating endpoints (behind explicit methods only)

## Getting Started

### Prerequisites

- Python 3.10+
- A Zerodha account with TOTP

### Installation

```bash
cd ~/Desktop/Projects/trading/coin-zerodha-api-client
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

### Auth

Coin reuses a Kite web login session. The client:

1. Logs into `https://kite.zerodha.com/api/login` with user id/password.
2. Submits TOTP to `https://kite.zerodha.com/api/twofa`.
3. Visits `https://coin.zerodha.com/login`, which establishes `coin_session`.
4. Uses the `public_token` cookie as the `X-CSRFToken` header for `/api/...` requests.

Credentials can be loaded from the existing Auto_Trader `my_secrets.py` file.
Default secrets path: `~/Desktop/Stocks/Auto_Trader/my_secrets.py`. Override with
`--secrets` or `COIN_ZERODHA_SECRETS`.

```bash
python -m coin_zerodha.cli profile
python -m coin_zerodha.cli holdings --secrets ~/Desktop/Stocks/Auto_Trader/my_secrets.py
COIN_ZERODHA_SECRETS=~/secure/my_secrets.py python -m coin_zerodha.cli sips
```

### Multi-Account Support

Define an `ACCOUNTS` dict in your secrets file:

```python
ACCOUNTS = {
    "alice": {"USER_NAME": "U123", "PASS": "your-password", "TOTP_KEY": "your-totp-secret"},
    "bob":   {"USER_NAME": "U456", "PASS": "his-password", "TOTP_KEY": "his-totp-secret"},
}
```

Then select the account via CLI:

```bash
coin-zerodha --account alice holdings
coin-zerodha --account bob profile
```

Or set `COIN_ZERODHA_ACCOUNT`. The old flat-vars format (`USER_NAME`, `PASS`,
`TOTP_KEY`) continues to work and is treated as the default account.

### Secrets file formats

Flat vars (backward compatible):

```python
USER_NAME = "U123"
PASS = "pw"
TOTP_KEY = "totp"
```

Named accounts (multi-account):

```python
ACCOUNTS = {
    "alice": {"USER_NAME": "U123", "PASS": "pw1", "TOTP_KEY": "totp1"},
    "bob":   {"USER_NAME": "U456", "PASS": "pw2", "TOTP_KEY": "totp2"},
}
```

### Safety

Unit tests mock HTTP; they do not hit Zerodha or print secrets. Mutating
endpoints exist behind explicit methods only; the initial CLI exposes read-only
smoke commands.

## Roadmap

- [x] v0.1 – Read-only smoke commands (profile, holdings, sips)
- [ ] v0.2 – Mutating endpoints
- [ ] v1.0 – Full client

See the open issues for the full list of proposed features and known bugs.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and
follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Contact

Sahil Goel – [@The-Great-One](https://github.com/The-Great-One) –
sahilgoel187@gmail.com

Project link: [https://github.com/The-Great-One/coin-zerodha-api-client](https://github.com/The-Great-One/coin-zerodha-api-client)

## Acknowledgments

- [Img Shields](https://shields.io)
- [Contributor Covenant](https://www.contributor-covenant.org)
