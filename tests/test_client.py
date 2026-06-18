import requests

from coin_zerodha.client import CoinAPIError, CoinAuthError, CoinClient
from coin_zerodha.credentials import CoinCredentials


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text="", url="https://example.test"):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.url = url

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/login"):
            self.cookies.set("coin_session", "coin", domain="coin.zerodha.com")
            self.cookies.set("public_token", "public", domain=".zerodha.com")
            return DummyResponse(200, {}, url="https://coin.zerodha.com/dashboard")
        return DummyResponse(200, {})

    def post(self, url, data=None, headers=None, **kwargs):
        self.calls.append(("POST", url, {"data": data, "headers": headers, **kwargs}))
        if url.endswith("/api/login"):
            return DummyResponse(200, {"status": "success", "data": {"request_id": "REQ"}})
        if url.endswith("/api/twofa"):
            self.cookies.set("enctoken", "enc", domain="kite.zerodha.com")
            self.cookies.set("public_token", "public", domain=".zerodha.com")
            return DummyResponse(200, {"status": "success", "data": {"profile": {}}})
        raise AssertionError(url)

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append((method, url, {"headers": headers, **kwargs}))
        return DummyResponse(200, {"status": "success", "data": {"ok": True}})


def test_login_establishes_coin_session(monkeypatch):
    monkeypatch.setattr("coin_zerodha.client.otp.get_totp", lambda key: "123456")
    session = FakeSession()
    client = CoinClient(CoinCredentials("U", "P", "T"), session=session)

    client.login()

    assert client.is_logged_in()
    posted_twofa = [c for c in session.calls if c[0] == "POST" and c[1].endswith("/api/twofa")][0]
    assert posted_twofa[2]["data"]["twofa_value"] == "123456"


def test_request_adds_public_token_as_csrf():
    session = FakeSession()
    session.cookies.set("public_token", "public", domain=".zerodha.com")
    client = CoinClient(CoinCredentials("U", "P", "T"), session=session)

    data = client.profile()

    assert data == {"ok": True}
    request_call = session.calls[-1]
    assert request_call[1] == "https://coin.zerodha.com/api/profile"
    assert request_call[2]["headers"]["X-CSRFToken"] == "public"


def test_api_error_raises_with_status_code():
    class ErrorSession(FakeSession):
        def request(self, method, url, headers=None, **kwargs):
            return DummyResponse(403, {"status": "error", "message": "Forbidden"}, text="Forbidden")

    client = CoinClient(CoinCredentials("U", "P", "T"), session=ErrorSession())

    try:
        client.profile()
    except CoinAPIError as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("expected CoinAPIError")


def test_login_failure_does_not_leak_password():
    class BadLoginSession(FakeSession):
        def post(self, url, data=None, headers=None, **kwargs):
            return DummyResponse(200, {"status": "error", "message": "Invalid credentials", "data": {}})

    client = CoinClient(CoinCredentials("U", "super-secret-password", "T"), session=BadLoginSession())

    try:
        client.login()
    except CoinAuthError as exc:
        assert "super-secret-password" not in str(exc)
    else:
        raise AssertionError("expected CoinAuthError")
