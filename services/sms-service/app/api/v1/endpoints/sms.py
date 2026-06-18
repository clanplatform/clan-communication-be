from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.sms_log import SmsLog
from app.schemas.sms import SendSmsRequest, SmsLogRead
from app.services.sms_provider import SmsProviderService

router = APIRouter(prefix="/send", tags=["sms"])


@router.post("", response_model=SmsLogRead, status_code=status.HTTP_202_ACCEPTED)
async def send_sms(
    request: SendSmsRequest,
    db: AsyncSession = Depends(get_db),
) -> SmsLogRead:
    svc = SmsProviderService(db)
    log = await svc.send(
        notification_id=request.notification_id,
        tenant_id=request.tenant_id,
        to_number=request.to_number,
        body=request.body,
        from_number=request.from_number,
    )
    return SmsLogRead.model_validate(log)


@router.get("/logs/{notification_id}", response_model=list[SmsLogRead])
async def get_sms_logs(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SmsLogRead]:
    result = await db.execute(
        select(SmsLog)
        .where(SmsLog.notification_id == notification_id)
        .order_by(SmsLog.created_at.desc())
    )
    return [SmsLogRead.model_validate(r) for r in result.scalars().all()]
