from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_tenant_id, verify_api_key
from app.models.template import NotificationTemplate
from app.schemas.template import TemplateCreate, TemplateRead

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    tmpl = NotificationTemplate(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        **payload.model_dump(),
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return TemplateRead.model_validate(tmpl)


@router.get("", response_model=list[TemplateRead])
async def list_templates(
    channel: str | None = None,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateRead]:
    q = select(NotificationTemplate).where(
        NotificationTemplate.tenant_id == tenant_id,
        NotificationTemplate.is_active.is_(True),
    )
    if channel:
        q = q.where(NotificationTemplate.channel == channel)
    rows = (await db.execute(q)).scalars().all()
    return [TemplateRead.model_validate(r) for r in rows]


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    result = await db.execute(
        select(NotificationTemplate).where(
            NotificationTemplate.id == template_id,
            NotificationTemplate.tenant_id == tenant_id,
        )
    )
    tmpl = result.scalar_one_or_none()
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return TemplateRead.model_validate(tmpl)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await db.execute(
        select(NotificationTemplate).where(
            NotificationTemplate.id == template_id,
            NotificationTemplate.tenant_id == tenant_id,
        )
    )
    tmpl = result.scalar_one_or_none()
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    tmpl.is_active = False
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
