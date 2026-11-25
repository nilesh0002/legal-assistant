"""
Tests for production CORS origin allow-listing and proxy-aware IP rate limiting.
"""

from types import SimpleNamespace
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.main import (
    MAX_REQUESTS_PER_WINDOW,
    _ip_request_counts,
    app,
    get_allowed_origins,
    get_real_client_ip,
)


def _make_fake_request(peer_host: str, headers_dict: dict):
    return SimpleNamespace(
        client=SimpleNamespace(host=peer_host),
        headers=Headers(headers_dict),
    )


def test_allowed_origins_env_and_wildcard_rejection(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    defaults = get_allowed_origins()
    assert "https://legal-assistant-web-rho.vercel.app" in defaults
    assert "*" not in defaults

    monkeypatch.setenv("ALLOWED_ORIGINS", "*, https://custom.vercel.app/, http://localhost:5173")
    custom = get_allowed_origins()
    assert "*" not in custom
    assert custom == ["https://custom.vercel.app", "http://localhost:5173"]


def test_cors_allows_vercel_and_blocks_unknown_origin():
    client = TestClient(app)

    ok_resp = client.get("/health", headers={"Origin": "https://legal-assistant-web-rho.vercel.app"})
    assert ok_resp.status_code == 200
    assert ok_resp.headers.get("access-control-allow-origin") == "https://legal-assistant-web-rho.vercel.app"

    blocked_resp = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert blocked_resp.status_code == 200
    assert "access-control-allow-origin" not in blocked_resp.headers


def test_real_client_ip_behind_trusted_proxy(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")

    req_xff = _make_fake_request("10.0.0.5", {"x-forwarded-for": "203.0.113.42, 10.0.0.5"})
    assert get_real_client_ip(req_xff) == "203.0.113.42"

    req_cf = _make_fake_request("127.0.0.1", {"cf-connecting-ip": "198.51.100.7", "x-forwarded-for": "203.0.113.42"})
    assert get_real_client_ip(req_cf) == "198.51.100.7"

    # Untrusted public peer cannot spoof forwarded headers
    req_spoof = _make_fake_request("8.8.8.8", {"x-forwarded-for": "1.2.3.4"})
    assert get_real_client_ip(req_spoof) == "8.8.8.8"


def test_rate_limit_isolates_forwarded_client_ips():
    _ip_request_counts.clear()
    client = TestClient(app)

    ip_a = "203.0.113.10"
    ip_b = "203.0.113.20"

    # Exhaust limit for ip_a
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        r = client.get("/search?q=Article+21", headers={"X-Forwarded-For": f"{ip_a}, 10.0.0.1"})
        assert r.status_code == 200

    # Next request from ip_a is rate-limited (429)
    blocked = client.get("/search?q=Article+21", headers={"X-Forwarded-For": f"{ip_a}, 10.0.0.1"})
    assert blocked.status_code == 429

    # Request from ip_b behind the same proxy still succeeds
    allowed_b = client.get("/search?q=Article+21", headers={"X-Forwarded-For": f"{ip_b}, 10.0.0.1"})
    assert allowed_b.status_code == 200

    _ip_request_counts.clear()
