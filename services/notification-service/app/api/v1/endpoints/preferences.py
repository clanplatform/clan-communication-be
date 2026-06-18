from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_tenant_id, verify_api_key
from app.models.preference import NotificationPreference
from app.schemas.preference import PreferenceCreate, PreferenceRead, PreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.put("/{recipient_id}", response_model=PreferenceRead)
async def upsert_preference(
    recipient_id: str,
    payload: PreferenceCreate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> PreferenceRead:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.tenant_id == tenant_id,
            NotificationPreference.recipient_id == recipient_id,
        )
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            **payload.model_dump(),
        )
        db.add(pref)
    else:
        for k, v in payload.model_dump(exclude_none=True).items():
            setattr(pref, k, v)
    await db.commit()
    await db.refresh(pref)
    return PreferenceRead.model_validate(pref)


@router.get("/{recipient_id}", response_model=PreferenceRead)
async def get_preference(
    recipient_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> PreferenceRead:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.tenant_id == tenant_id,
            NotificationPreference.recipient_id == recipient_id,
        )
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    return PreferenceRead.model_validate(pref)


@router.patch("/{recipient_id}", response_model=PreferenceRead)
async def update_preference(
    recipient_id: str,
    payload: PreferenceUpdate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> PreferenceRead:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.tenant_id == tenant_id,
            NotificationPreference.recipient_id == recipient_id,
        )
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pref, k, v)
    await db.commit()
    await db.refresh(pref)
    return PreferenceRead.model_validate(pref)
