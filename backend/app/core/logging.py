import re
from logging import (  # type: ignore[attr-defined]
    INFO,
    Formatter,
    Logger,
    LogRecord,
    StreamHandler,
    getLogger,
)

from backend.app.core.config import settings

# Patterns for sensitive health or personal data
PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(password|token|secret|key)=['\"]?[^'\"\s]+['\"]?", re.IGNORECASE), r"\1=[REDACTED]"),
]


class HIPAASanitizingFormatter(Formatter):
    """
    Log formatter that redacts personally identifiable information (PII)
    and protected health information (PHI) before emission.
    """

    def format(self, record: LogRecord) -> str:
        msg = super().format(record)
        if settings.ENABLE_HIPAA_LOG_REDACTION:
            for pattern, replacement in PII_PATTERNS:
                msg = pattern.sub(replacement, msg)
        return msg


def get_logger(name: str) -> Logger:
    logger = getLogger(name)
    if not logger.handlers:
        handler = StreamHandler()
        formatter = HIPAASanitizingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(INFO)
    return logger


audit_logger = get_logger("audit.hipaa")
app_logger = get_logger("speech_therapy")
