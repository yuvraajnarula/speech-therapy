import pytest
from fastapi import HTTPException
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
    require_roles,
    TokenPayload,
)


def test_password_hashing():
    raw = "SecurePassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_lifecycle():
    token = create_access_token(subject="user_123", role="therapist")
    payload = decode_access_token(token)
    assert payload.sub == "user_123"
    assert payload.role == "therapist"


@pytest.mark.asyncio
async def test_require_roles_permission():
    therapist_checker = require_roles(["therapist", "admin"])

    # Allowed role
    user_payload = TokenPayload(sub="user_1", role="therapist", exp=9999999999)
    res = await therapist_checker(current_user=user_payload)
    assert res.sub == "user_1"

    # Forbidden role
    patient_payload = TokenPayload(sub="user_2", role="patient", exp=9999999999)
    with pytest.raises(HTTPException) as exc_info:
        await therapist_checker(current_user=patient_payload)
    assert exc_info.value.status_code == 403
