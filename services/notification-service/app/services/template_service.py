from __future__ import annotations

from typing import Any

from jinja2 import Environment, BaseLoader, TemplateNotFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.template import NotificationTemplate
from libs.communication_shared.exceptions import TemplateNotFoundError

import logging

logger = logging.getLogger(__name__)


class TemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._jinja_env = Environment(loader=BaseLoader(), autoescape=True)

    async def render(
        self,
        tenant_id: str,
        template_id: str,
        channel: str,
        variables: dict[str, Any],
    ) -> dict[str, str]:
        result = await self._db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == template_id,
                NotificationTemplate.tenant_id == tenant_id,
                NotificationTemplate.channel == channel,
                NotificationTemplate.is_active.is_(True),
            )
        )
        tmpl = result.scalar_one_or_none()
        if tmpl is None:
            raise TemplateNotFoundError(template_id)

        rendered: dict[str, str] = {}
        rendered["body"] = self._jinja_env.from_string(tmpl.body_template).render(
            **variables
        )
        if tmpl.subject_template:
            rendered["subject"] = self._jinja_env.from_string(
                tmpl.subject_template
            ).render(**variables)
        return rendered

    async def get_by_slug(
        self, tenant_id: str, slug: str, channel: str, language: str = "en"
    ) -> NotificationTemplate | None:
        result = await self._db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.tenant_id == tenant_id,
                NotificationTemplate.slug == slug,
                NotificationTemplate.channel == channel,
                NotificationTemplate.language == language,
                NotificationTemplate.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()
