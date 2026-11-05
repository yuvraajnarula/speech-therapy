"""
Tests for backend/app/core/security.py — JWT auth + enterprise OIDC/JWKS.

Covers: password hashing/verification, access token creation/decoding,
OIDC role mapping, require_roles RBAC, and OIDC fallback chain.
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

import asyncio
import pytest

from backend.app.core.security import (
    TokenPayload,
    create_access_token,
    decode_access_token,
    decode_oidc_token,
    get_oidc_issuer,
    get_oidc_jwks_url,
    get_oidc_client_id,
    oidc_enabled_providers,
    clinician_email_domains,
    require_roles,
    verify_password,
    get_password_hash,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def test_verify_password_roundtrip():
    pw = "super-secret-clinical-password-123"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_bcrypt_limit():
    """Bcrypt only hashes first 72 bytes; long passwords are truncated."""
    pw = "a" * 100
    hashed = get_password_hash(pw)
    assert verify_password(pw[:72], hashed) is True
    assert verify_password(pw[:71] + "z", hashed) is False


# ---------------------------------------------------------------------------
# Access token (HS256 platform JWT)
# ---------------------------------------------------------------------------

def test_create_and_decode_access_token():
    token = create_access_token(subject="user-42", role="therapist")
    payload = asyncio.run(decode_access_token(token))
    assert payload.sub == "user-42"
    assert payload.role == "therapist"
    assert payload.exp > 0


def test_create_access_token_custom_expiry():
    token = create_access_token(subject="user-42", role="patient",
                                expires_delta=timedelta(minutes=5))
    payload = asyncio.run(decode_access_token(token))
    assert payload.sub == "user-42"
    assert payload.role == "patient"


def test_decode_access_token_invalid():
    with pytest.raises(Exception):
        asyncio.run(decode_access_token("not-a-valid-token"))


def test_decode_access_token_empty():
    with pytest.raises(Exception):
        asyncio.run(decode_access_token(""))


# ---------------------------------------------------------------------------
# OIDC config accessors
# ---------------------------------------------------------------------------

def test_oidc_accessors_defaults():
    assert oidc_enabled_providers() == []
    assert clinician_email_domains() == []
    assert get_oidc_jwks_url("auth0") is None
    assert get_oidc_client_id("auth0") is None
    assert get_oidc_issuer("auth0") is None


# ---------------------------------------------------------------------------
# OIDC role mapping
# ---------------------------------------------------------------------------

from backend.app.core.security import _map_oidc_role  # noqa: E402


def test_map_oidc_role_explicit_claim():
    assert _map_oidc_role({"role": "therapist"}, "a@b.com") == "therapist"
    assert _map_oidc_role({"role": "admin"}, "a@b.com") == "admin"
    assert _map_oidc_role({"role": "patient"}, "a@b.com") == "patient"


def test_map_oidc_role_list_claim():
    assert _map_oidc_role({"role": ["admin"]}, "a@b.com") == "admin"


def test_map_oidc_role_groups_claim():
    assert _map_oidc_role({"groups": ["clinicians-group"]}, "a@b.com") == "therapist"
    assert _map_oidc_role({"groups": ["admins-group"]}, "a@b.com") == "admin"


def test_map_oidc_role_email_domain_clinician(monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "CLINICIAN_EMAIL_DOMAINS", "hospital.org,clinic.net")
    assert _map_oidc_role({}, "dr.smith@hospital.org") == "therapist"
    assert _map_oidc_role({}, "patient@gmail.com") == "patient"


def test_map_oidc_role_default_patient():
    assert _map_oidc_role({}, "anyone@example.com") == "patient"


# ---------------------------------------------------------------------------
# require_roles RBAC
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_roles_allows():
    checker = require_roles(["therapist", "admin"])
    user = TokenPayload(sub="u1", role="therapist", exp=9999999999)
    result = await checker(current_user=user)
    assert result.role == "therapist"


@pytest.mark.asyncio
async def test_require_roles_denies():
    checker = require_roles(["admin"])
    user = TokenPayload(sub="u1", role="patient", exp=9999999999)
    with pytest.raises(Exception):
        await checker(current_user=user)


# ---------------------------------------------------------------------------
# decode_oidc_token (mocked JWKS)
# ---------------------------------------------------------------------------

def _fake_jwks():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import jwt

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Build a JWK from the public key
    from jwt.algorithms import RSAAlgorithm
    public_key_obj = serialization.load_pem_public_key(public_pem)
    jwk = RSAAlgorithm.to_jwk(public_key_obj)
    import json
    jwk_dict = json.loads(jwk)
    jwk_dict["kid"] = "test-kid-1"
    jwk_dict["kty"] = "RSA"
    jwk_dict["use"] = "sig"

    # Sign a token with the private key
    token = jwt.encode(
        {"sub": "oidc-user", "role": "therapist", "email": "dr@hospital.org",
         "iss": "https://hospital.auth0.com/", "aud": "my-client-id",
         "exp": 9999999999},
        private_key,
        algorithm="RS256",
        headers={"kid": "test-kid-1"},
    )
    return token, {"keys": [jwk_dict]}, "https://hospital.auth0.com/", "my-client-id"


@pytest.mark.asyncio
async def test_decode_oidc_token_success(monkeypatch):
    token, jwks, issuer, audience = _fake_jwks()

    async def fake_fetch(provider, url):
        return jwks

    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "OIDC_JWKS_URLS", '{"hospital": "https://hospital.auth0.com/.well-known/jwks.json"}')
    monkeypatch.setattr(cfg.settings, "OIDC_CLIENT_IDS", '{"hospital": "my-client-id"}')
    monkeypatch.setattr(cfg.settings, "OIDC_ISSUERS", '{"hospital": "https://hospital.auth0.com/"}')
    monkeypatch.setattr(cfg.settings, "OIDC_ENABLED_PROVIDERS", "hospital")

    with patch("backend.app.core.security._fetch_jwks", side_effect=fake_fetch):
        payload = await decode_oidc_token(token, "hospital")
        assert payload is not None
        assert payload.sub == "oidc-user"
        assert payload.role == "therapist"


@pytest.mark.asyncio
async def test_decode_oidc_token_no_jwks_url(monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "OIDC_JWKS_URLS", "{}")
    payload = await decode_oidc_token("some-token", "unknown-provider")
    assert payload is None


# ---------------------------------------------------------------------------
# decode_access_token falls back to OIDC
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_decode_access_token_oidc_fallback(monkeypatch):
    token, jwks, issuer, audience = _fake_jwks()

    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "OIDC_JWKS_URLS", '{"hospital": "https://hospital.auth0.com/.well-known/jwks.json"}')
    monkeypatch.setattr(cfg.settings, "OIDC_CLIENT_IDS", '{"hospital": "my-client-id"}')
    monkeypatch.setattr(cfg.settings, "OIDC_ISSUERS", '{"hospital": "https://hospital.auth0.com/"}')
    monkeypatch.setattr(cfg.settings, "OIDC_ENABLED_PROVIDERS", "hospital")

    async def fake_fetch(provider, url):
        return jwks

    with patch("backend.app.core.security._fetch_jwks", side_effect=fake_fetch):
        # Not a valid HS256 token -> falls through to OIDC
        payload = await decode_access_token(token)
        assert payload is not None
        assert payload.sub == "oidc-user"
        assert payload.role == "therapist"
