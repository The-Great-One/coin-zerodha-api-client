from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import time

import onetimepass as otp
import requests

from .credentials import CoinCredentials
from .endpoints import COIN_ENDPOINTS


class CoinError(RuntimeError):
    pass


class CoinAuthError(CoinError):
    pass


class CoinAPIError(CoinError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(frozen=True)
class CoinResponse:
    status: str
    data: Any
    raw: Mapping[str, Any]


class CoinClient:
    kite_base_url = "https://kite.zerodha.com"
    coin_base_url = "https://coin.zerodha.com"

    def __init__(self, credentials: CoinCredentials, *, session: requests.Session | None = None, timeout: float = 20.0):
        self.credentials = credentials
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def login(self) -> None:
        """Login through Kite and establish a Coin web session."""
        last_totp_error: tuple[requests.Response, Mapping[str, Any]] | None = None
        for attempt in range(2):
            if attempt:
                # Zerodha can reject a TOTP reused within the same 30s window.
                # Wait for the next code rather than immediately burning another attempt.
                time.sleep(31)
            self.session.get(f"{self.kite_base_url}/", timeout=self.timeout)
            api_headers = {
                "Referer": f"{self.kite_base_url}/",
                "Origin": self.kite_base_url,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            login_payload = {"user_id": self.credentials.user_id, "password": self.credentials.password}
            login_resp = self.session.post(f"{self.kite_base_url}/api/login", data=login_payload, headers=api_headers, timeout=self.timeout)
            login_json = self._json(login_resp)
            request_id = (login_json.get("data") or {}).get("request_id")
            if login_resp.status_code != 200 or not request_id:
                raise CoinAuthError(self._auth_summary("Kite login failed", login_resp, login_json))

            twofa_payload = {
                "user_id": self.credentials.user_id,
                "request_id": request_id,
                "twofa_value": otp.get_totp(self.credentials.totp_key),
                "twofa_type": "totp",
            }
            twofa_resp = self.session.post(f"{self.kite_base_url}/api/twofa", data=twofa_payload, headers=api_headers, timeout=self.timeout)
            twofa_json = self._json(twofa_resp)
            if twofa_resp.status_code == 200 and twofa_json.get("status") == "success":
                break
            if self._is_invalid_totp(twofa_json) and attempt == 0:
                last_totp_error = (twofa_resp, twofa_json)
                continue
            raise CoinAuthError(self._auth_summary("Kite TOTP failed", twofa_resp, twofa_json))
        else:
            if last_totp_error:
                raise CoinAuthError(self._auth_summary("Kite TOTP failed", last_totp_error[0], last_totp_error[1]))
            raise CoinAuthError("Kite TOTP failed")

        coin_resp = self.session.get(f"{self.coin_base_url}/login", allow_redirects=True, timeout=self.timeout)
        if coin_resp.status_code >= 400 or not self.session.cookies.get("coin_session"):
            raise CoinAuthError(f"Coin login failed: status_code={coin_resp.status_code}, url={coin_resp.url}")

    def is_logged_in(self) -> bool:
        return bool(self.session.cookies.get("coin_session") and self.session.cookies.get("public_token"))

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Call a Coin API path and return its `data` payload."""
        if path.startswith("http"):
            url = path
        else:
            url = f"{self.coin_base_url}{path}"
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json, text/plain, */*")
        headers.setdefault("Referer", f"{self.coin_base_url}/")
        public_token = self.session.cookies.get("public_token")
        if public_token:
            headers.setdefault("X-CSRFToken", public_token)
        resp = self.session.request(method.upper(), url, headers=headers, timeout=self.timeout, **kwargs)
        payload = self._json(resp)
        if resp.status_code >= 400:
            raise CoinAPIError(f"Coin API HTTP {resp.status_code}: {payload.get('message') or resp.text[:120]}", status_code=resp.status_code, payload=payload)
        if isinstance(payload, dict) and payload.get("status") and payload.get("status") != "success":
            raise CoinAPIError(f"Coin API error: {payload.get('message') or payload.get('status')}", status_code=resp.status_code, payload=payload)
        return payload.get("data") if isinstance(payload, dict) and "data" in payload else payload

    def get_endpoint(self, name: str, **params: Any) -> Any:
        try:
            template = COIN_ENDPOINTS[name]
        except KeyError as exc:
            raise KeyError(f"Unknown endpoint {name!r}; known={sorted(COIN_ENDPOINTS)}") from exc
        return self.request("GET", template.format(**params))

    def profile(self) -> Any:
        return self.get_endpoint("profile")

    def holdings(self) -> Any:
        return self.get_endpoint("holdings")

    def orders(self, *, from_date: str | None = None, to_date: str | None = None) -> Any:
        if from_date and to_date:
            return self.get_endpoint("orders_range", from_date=from_date, to_date=to_date)
        return self.get_endpoint("orders")

    def sips(self) -> Any:
        return self.get_endpoint("sips")

    def watchlist(self) -> Any:
        return self.get_endpoint("watchlist")

    @staticmethod
    def _json(resp: requests.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _is_invalid_totp(payload: Mapping[str, Any]) -> bool:
        message = str(payload.get("message") or "").lower()
        return "invalid totp" in message

    @staticmethod
    def _auth_summary(prefix: str, resp: requests.Response, payload: Mapping[str, Any]) -> str:
        data = payload.get("data")
        keys = sorted(data.keys()) if isinstance(data, dict) else []
        return f"{prefix}: status_code={resp.status_code}, api_status={payload.get('status')!r}, message={payload.get('message')!r}, data_keys={keys}"
