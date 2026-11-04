"""
Memory API endpoints for IndicAST Clinical Speech Therapy Platform.

Provides read/write access to the per-patient clinical memory layer.
Protected by JWT RBAC — therapists and admins can read any patient's memory.
Patients can only read their own memory.

Endpoints:
  GET  /api/v1/memory/{patient_id}        — Fetch full PatientMemory
  GET  /api/v1/memory/{patient_id}/tutor  — Fetch compact TutorContext
  POST /api/v1/memory/{patient_id}/reset  — Reset memory (HIPAA deletion)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import TokenPayload, decode_access_token
from backend.app.db.session import get_db
from backend.app.services.memory_service import memory_service, PatientMemory, TutorContext

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/memory", tags=["Patient Memory"])

_bearer = HTTPBearer(auto_error=False)


async def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenPayload:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return await decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _authorize(current_user: TokenPayload, patient_id: str) -> None:
    """Patients can only access their own memory; therapists/admins can access any."""
    if current_user.role == "patient" and current_user.sub != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients may only access their own memory records",
        )


@router.get("/{patient_id}", response_model=PatientMemory)
async def get_patient_memory(
    patient_id: str,
    dialect: str = Query("hi", regex="^(hi|kn|ta|te|en-IN)$"),
    current_user: TokenPayload = Depends(_get_current_user),
    _db: AsyncSession = Depends(get_db),
) -> PatientMemory:
    """
    Retrieve full clinical memory for a patient+dialect pair.
    Includes phoneme error map, mastery scores, weak phoneme ranking, and recent utterances.
    """
    _authorize(current_user, patient_id)
    return await memory_service.get_memory(patient_id, dialect)


@router.get("/{patient_id}/tutor", response_model=TutorContext)
async def get_tutor_context(
    patient_id: str,
    dialect: str = Query("hi", regex="^(hi|kn|ta|te|en-IN)$"),
    current_user: TokenPayload = Depends(_get_current_user),
    _db: AsyncSession = Depends(get_db),
) -> TutorContext:
    """
    Retrieve a compact TutorContext snapshot used by the Live Tutor WebSocket
    to select the next adaptive drill target.
    """
    _authorize(current_user, patient_id)
    return await memory_service.get_tutor_context(patient_id, dialect)


@router.post("/{patient_id}/reset", response_model=PatientMemory)
async def reset_patient_memory(
    patient_id: str,
    dialect: str = Query("hi", regex="^(hi|kn|ta|te|en-IN)$"),
    current_user: TokenPayload = Depends(_get_current_user),
    _db: AsyncSession = Depends(get_db),
) -> PatientMemory:
    """
    Reset all clinical memory for a patient+dialect pair.
    Restricted to therapist and admin roles (HIPAA deletion pathway).
    """
    if current_user.role not in ("therapist", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only therapists and admins may reset patient memory",
        )
    return await memory_service.reset_memory(patient_id, dialect)
