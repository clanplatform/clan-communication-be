from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.email_log import EmailLog
from app.schemas.email import SendEmailRequest, EmailLogRead
from app.services.email_provider import EmailProviderService

router = APIRouter(prefix="/send", tags=["email"])


@router.post("", response_model=EmailLogRead, status_code=status.HTTP_202_ACCEPTED)
async def send_email(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailLogRead:
    svc = EmailProviderService(db)
    log = await svc.send(request)
    return EmailLogRead.model_validate(log)


@router.get("/logs/{notification_id}", response_model=list[EmailLogRead])
async def get_email_logs(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[EmailLogRead]:
    result = await db.execute(
        select(EmailLog)
        .where(EmailLog.notification_id == notification_id)
        .order_by(EmailLog.created_at.desc())
    )
    rows = result.scalars().all()
    return [EmailLogRead.model_validate(r) for r in rows]
