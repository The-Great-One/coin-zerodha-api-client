from coin_zerodha.endpoints import COIN_ENDPOINTS


def test_discovered_core_coin_endpoints_are_present():
    expected = {
        "profile",
        "holdings",
        "holding_detail",
        "portfolio_xirr",
        "orders",
        "orders_range",
        "sips",
        "gtt",
        "stp",
        "swp",
        "mandates_iccl",
        "watchlist",
        "nps_profile",
        "nps_portfolio",
    }

    assert expected <= set(COIN_ENDPOINTS)


def test_all_endpoint_templates_are_api_paths():
    assert COIN_ENDPOINTS
    for path in COIN_ENDPOINTS.values():
        assert path.startswith("/api/")


def test_parameterized_endpoint_templates_format_cleanly():
    formatted = {
        "holding_detail": COIN_ENDPOINTS["holding_detail"].format(isin="INF123"),
        "holding_xirr": COIN_ENDPOINTS["holding_xirr"].format(isin="INF123"),
        "orders_range": COIN_ENDPOINTS["orders_range"].format(from_date="2026-01-01", to_date="2026-01-31"),
        "order_detail": COIN_ENDPOINTS["order_detail"].format(order_id="OID"),
        "sip_detail": COIN_ENDPOINTS["sip_detail"].format(sip_id="SIP"),
        "gtt_detail": COIN_ENDPOINTS["gtt_detail"].format(gtt_id="GTT"),
        "stp_detail": COIN_ENDPOINTS["stp_detail"].format(stp_id="STP"),
        "swp_detail": COIN_ENDPOINTS["swp_detail"].format(swp_id="SWP"),
        "watchlist_detail": COIN_ENDPOINTS["watchlist_detail"].format(watchlist_id="WL"),
    }

    assert formatted["holding_detail"] == "/api/mf/holdings/INF123"
    assert formatted["orders_range"] == "/api/mf/orders?from=2026-01-01&to=2026-01-31"
    assert all("{" not in value and "}" not in value for value in formatted.values())
