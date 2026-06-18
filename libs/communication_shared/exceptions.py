class CommunicationError(Exception):
    """Base exception for all communication errors."""

    def __init__(self, message: str, code: str = "COMMUNICATION_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class TenantNotFoundError(CommunicationError):
    def __init__(self, tenant_id: str) -> None:
        super().__init__(f"Tenant '{tenant_id}' not found", "TENANT_NOT_FOUND")
        self.tenant_id = tenant_id


class ProviderError(CommunicationError):
    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"Provider '{provider}' error: {detail}", "PROVIDER_ERROR")
        self.provider = provider


class RateLimitError(CommunicationError):
    def __init__(self, tenant_id: str, limit: int) -> None:
        super().__init__(
            f"Rate limit {limit}/min exceeded for tenant '{tenant_id}'",
            "RATE_LIMIT_EXCEEDED",
        )
        self.tenant_id = tenant_id
        self.limit = limit


class TemplateNotFoundError(CommunicationError):
    def __init__(self, template_id: str) -> None:
        super().__init__(f"Template '{template_id}' not found", "TEMPLATE_NOT_FOUND")
        self.template_id = template_id


class InvalidPayloadError(CommunicationError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Invalid payload: {detail}", "INVALID_PAYLOAD")
