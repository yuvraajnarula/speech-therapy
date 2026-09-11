from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    TokenPayload,
)
from backend.app.db.session import get_db
from backend.app.db.models import User, ConsentRecord
from backend.app.core.logging import audit_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "patient"  # "therapist" or "patient"
    preferred_locale: str = "en-IN"


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class ConsentSchema(BaseModel):
    hipaa_acknowledged: bool
    audio_retention_agreed: bool
    research_sft_permitted: bool


@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(User.email == user_in.email)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role if user_in.role in ["therapist", "patient", "admin"] else "patient",
        preferred_locale=user_in.preferred_locale,
    )
    db.add(user)
    await db.flush()

    # Create default consent record
    consent = ConsentRecord(
        user_id=user.id,
        hipaa_acknowledged=True,
        audio_retention_agreed=False,
        research_sft_permitted=False
    )
    db.add(consent)
    await db.commit()
    await db.refresh(user)

    audit_logger.info(f"User registered: id={user.id}, role={user.role}")
    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(access_token=token, role=user.role, user_id=user.id)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        audit_logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    audit_logger.info(f"User login successful: id={user.id}")
    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(access_token=token, role=user.role, user_id=user.id)


@router.get("/me")
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == current_user.sub)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "preferred_locale": user.preferred_locale,
        "created_at": user.created_at,
    }


@router.post("/consent")
async def update_consent(
    consent_in: ConsentSchema,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ConsentRecord).where(ConsentRecord.user_id == current_user.sub)
    res = await db.execute(stmt)
    consent = res.scalars().first()

    if not consent:
        consent = ConsentRecord(user_id=current_user.sub)
        db.add(consent)

    consent.hipaa_acknowledged = consent_in.hipaa_acknowledged
    consent.audio_retention_agreed = consent_in.audio_retention_agreed
    consent.research_sft_permitted = consent_in.research_sft_permitted
    await db.commit()

    audit_logger.info(f"Updated consent preferences for user id={current_user.sub}")
    return {"status": "success", "message": "Consent preferences recorded."}
