from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderSendResult:
    """Result of a successful provider send.

    message_id goes to email_logs.provider_message_id; details carries
    provider-specific extras when a provider has any.
    """

    message_id: str
    details: dict = field(default_factory=dict)
