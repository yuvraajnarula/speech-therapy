from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

try:
    import jwt
    from jwt import PyJWTError as JWTError
except ImportError:
    from jose import JWTError, jwt  # type: ignore[no-redef]
import bcrypt
import httpx
from pydantic import BaseModel

from backend.app.core.config import (
    clinician_email_domains,
    get_oidc_client_id,
    get_oidc_issuer,
    get_oidc_jwks_url,
    oidc_enabled_providers,
    settings,
)
from backend.app.core.logging import audit_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

# ---------------------------------------------------------------------------
# Enterprise OIDC / JWKS Identity Provider support
# ---------------------------------------------------------------------------
# Allows hospitals, schools, and private clinics to authenticate users via
# their existing identity providers (Google Workspace, Microsoft Entra ID /
# Azure AD, Auth0, AWS Cognito, Firebase) with role mapping for clinicians
# and patients.
# ---------------------------------------------------------------------------

# In-memory JWKS cache keyed by provider name
_JWKS_CACHE: dict[str, dict[str, Any]] = {}
_JWKS_TTL_SECONDS = 3600  # refresh JWKS every hour
_JWKS_LAST_FETCH: dict[str, datetime] = {}


async def _fetch_jwks(provider_name: str, jwks_url: str) -> dict[str, Any]:
    """
    Fetch the JSON Web Key Set (JWKS) from the identity provider.
    Cached in-memory to avoid hitting the IdP on every token validation.
    """
    cached = _JWKS_CACHE.get(provider_name)
    last_fetch = _JWKS_LAST_FETCH.get(provider_name)
    if cached and last_fetch:
        if (datetime.now(UTC) - last_fetch).total_seconds() < _JWKS_TTL_SECONDS:
            return cached

    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks = response.json()

    _JWKS_CACHE[provider_name] = jwks
    _JWKS_LAST_FETCH[provider_name] = datetime.now(UTC)
    return jwks


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


def _get_signing_key(token: str, jwks: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract the unverified header from the JWT to find the key ID (kid),
    then look up the matching public key in the JWKS.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        return None

    kid = unverified_header.get("kid")
    keys = jwks.get("keys", [])
    for key in keys:
        if key.get("kid") == kid or (not kid and key.get("kty") == "RSA"):
            return key
    return None


async def decode_oidc_token(token: str, provider_name: str) -> TokenPayload | None:
    """
    Validate a JWT issued by an enterprise OIDC identity provider using its
    JWKS endpoint. Returns a TokenPayload on success, None on failure.

    Supported providers:
      - Auth0
      - AWS Cognito
      - Firebase Auth
      - Google Workspace / Google Identity Platform
      - Microsoft Entra ID / Azure AD
    """
    jwks_url = get_oidc_jwks_url(provider_name)
    if not jwks_url:
        return None

    try:
        jwks = await _fetch_jwks(provider_name, jwks_url)
        signing_key = _get_signing_key(token, jwks)
        if not signing_key:
            audit_logger.warning(f"[OIDC] No matching signing key for provider={provider_name}")
            return None

        # Build a public key from the JWK for verification
        public_key = jwt.PyJWK(signing_key).key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=get_oidc_client_id(provider_name),
            issuer=get_oidc_issuer(provider_name),
            options={"verify_exp": True, "verify_aud": True, "verify_iss": True},
        )

        sub = payload.get("sub")
        email = payload.get("email", "")
        role = _map_oidc_role(payload, email)
        if not sub:
            return None

        audit_logger.info(f"[OIDC] Token validated for provider={provider_name}, sub={sub[:8]}..., role={role}")
        return TokenPayload(sub=sub, role=role, exp=payload.get("exp", 0))
    except Exception as e:
        audit_logger.warning(f"[OIDC] Token validation failed for provider={provider_name}: {e}")
        return None


def _map_oidc_role(payload: dict[str, Any], email: str) -> str:
    """
    Map enterprise identity provider claims to platform roles.

    Priority:
      1. Explicit `role` claim in token
      2. Group membership claims (e.g. Azure AD groups, Auth0 roles)
      3. Email domain allow-list for clinicians
      4. Default to "patient"
    """
    # 1. Explicit role claim
    role_claim = payload.get("role") or payload.get("https://claims.example.com/role")
    if role_claim:
        if isinstance(role_claim, list) and role_claim:
            role_claim = role_claim[0]
        if role_claim in ("therapist", "patient", "admin"):
            return role_claim

    # 2. Group membership claims
    groups = payload.get("groups") or payload.get("https://claims.microsoft.com/groups") or []
    if isinstance(groups, str):
        groups = [groups]
    for group in groups:
        if isinstance(group, str) and "clinician" in group.lower():
            return "therapist"
        if isinstance(group, str) and "admin" in group.lower():
            return "admin"

    # 3. Email domain allow-list for clinicians
    clinician_domains = clinician_email_domains()
    if clinician_domains and email:
        for domain in clinician_domains:
            if email.lower().endswith(domain.lower()):
                return "therapist"

    return "patient"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "role": role, "exp": int(expire.timestamp())}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate an access token.

    Supports two modes:
      1. Platform-issued HS256 JWT (default)
      2. Enterprise OIDC RS256 JWT (Auth0, Cognito, Firebase, Google, Azure AD)
         when the token fails HS256 validation and OIDC is enabled.

    OIDC validation uses JWKS endpoint verification with audience and issuer
    checks for defense-in-depth.
    """
    # Try platform HS256 token first
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = cast(str, payload.get("sub"))
        role: str = cast(str, payload.get("role"))
        exp: int = cast(int, payload.get("exp"))
        if sub is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenPayload(sub=sub, role=role, exp=exp)
    except JWTError:
        pass

    # Fall back to enterprise OIDC providers
    if oidc_enabled_providers():
        for provider in oidc_enabled_providers():
            oidc_payload = await decode_oidc_token(token, provider)
            if oidc_payload:
                return oidc_payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> TokenPayload:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await decode_access_token(token)


def require_roles(allowed_roles: list[str]):
    """Role-Based Access Control (RBAC) dependency factory."""
    async def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in allowed_roles:
            audit_logger.warning(
                f"Access denied for user {current_user.sub} with role {current_user.role}. "
                f"Required one of: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker
