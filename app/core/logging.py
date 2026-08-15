"""
Structured JSON logging via structlog.

Two things matter here beyond "make it JSON": every log call site should be
able to attach structured fields (request_id, model, latency_ms, ...)
instead of building strings, and secrets must never reach a log sink even
if a call site accidentally passes one. The `_redact_sensitive` processor
is a defense-in-depth backstop for the second point - application code
should still never log passwords/tokens/keys in the first place.
"""
import logging
import sys

import structlog

_SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "api_key",
    "key",
    "key_hash",
    "authorization",
    "jwt",
    "jwt_secret",
    "hf_api_token",
    "hf_glm_token",
    "hf_kimi_token",
    "secret",
    "database_url",
}


def _redact_sensitive(logger, method_name, event_dict):
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***redacted***"
    return event_dict


def configure_logging(*, debug: bool = False) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    # Quiet down noisy third-party loggers; our own structured logs carry
    # everything we need about requests, DB errors, etc.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            _redact_sensitive,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
