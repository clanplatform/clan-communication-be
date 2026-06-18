import hashlib
import uuid
from datetime import datetime, timezone


def generate_idempotency_key(tenant_id: str, payload: dict) -> str:
    raw = f"{tenant_id}:{sorted(payload.items())}"
    return hashlib.sha256(raw.encode()).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def mask_phone(phone: str) -> str:
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"


def slugify(text: str) -> str:
    return text.lower().strip().replace(" ", "-")
