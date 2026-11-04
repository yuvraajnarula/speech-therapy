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


@pytest.mark.asyncio
async def test_jwt_token_lifecycle():
    token = create_access_token(subject="user_123", role="therapist")
    payload = await decode_access_token(token)
    assert payload.sub == "user_123"
    assert payload.role == "therapist"


def test_require_roles_permission():
    therapist_checker = require_roles(["therapist", "admin"])

    # Allowed role
    user_payload = TokenPayload(sub="user_1", role="therapist", exp=9999999999)
    coro = therapist_checker(current_user=user_payload)
    try:
        coro.send(None)
        res = None
    except StopIteration as e:
        res = e.value
    assert res is not None
    assert res.sub == "user_1"

    # Forbidden role
    patient_payload = TokenPayload(sub="user_2", role="patient", exp=9999999999)
    with pytest.raises(HTTPException) as exc_info:
        coro2 = therapist_checker(current_user=patient_payload)
        coro2.send(None)
    assert exc_info.value.status_code == 403
