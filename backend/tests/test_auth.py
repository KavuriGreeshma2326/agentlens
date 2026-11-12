"""Tests for POST /auth/register, POST /auth/login, GET /auth/me."""

import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

_PAYLOAD = {"email": "alice@example.com", "password": "s3cr3t!"}


def _register(client, payload=None):
    return client.post("/auth/register", json=payload or _PAYLOAD)


def _login(client, payload=None):
    return client.post("/auth/login", json=payload or _PAYLOAD)


def _token(client):
    """Register and return the access token."""
    return _register(client).json()["access_token"]


# ── Register ─────────────────────────────────────────────────────────────────


def test_register_returns_201(client):
    assert _register(client).status_code == 201


def test_register_returns_bearer_token(client):
    data = _register(client).json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email_returns_400(client):
    _register(client)
    assert _register(client).status_code == 400


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_returns_200(client):
    _register(client)
    assert _login(client).status_code == 200


def test_login_returns_bearer_token(client):
    _register(client)
    data = _login(client).json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    _register(client)
    resp = _login(client, {"email": _PAYLOAD["email"], "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client):
    resp = _login(client, {"email": "ghost@example.com", "password": "x"})
    assert resp.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────


def test_me_returns_200(client):
    token = _token(client)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_me_returns_correct_email(client):
    token = _token(client)
    data = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert data["email"] == _PAYLOAD["email"]


def test_me_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401
