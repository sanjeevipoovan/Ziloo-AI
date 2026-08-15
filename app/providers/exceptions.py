class ProviderException(Exception):
    """Base class for provider-specific failures. A provider implementation
    must never let a raw vendor SDK exception escape - always catch and
    re-raise as one of these, so the orchestrator (app/orchestrator/execution.py)
    can translate into a MyAIException without knowing which vendor was involved."""


class ProviderTimeoutError(ProviderException):
    pass


class ProviderUnavailableError(ProviderException):
    pass


class ProviderAuthenticationError(ProviderException):
    pass


class ProviderResponseError(ProviderException):
    pass
