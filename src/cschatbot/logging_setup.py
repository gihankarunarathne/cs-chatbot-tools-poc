"""Process-wide logging configuration."""

import logging
import sys

from .config import settings

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s [%(session_id)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger("cschatbot")
    root.setLevel(settings.log_level.upper())
    root.addHandler(handler)
    root.propagate = False

    _CONFIGURED = True


class SessionLogAdapter(logging.LoggerAdapter):
    """Injects session_id into every log record so turns can be correlated."""

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})["session_id"] = self.extra.get("session_id", "-")
        return msg, kwargs


def get_logger(name: str, session_id: str | None = None) -> logging.LoggerAdapter:
    configure_logging()
    return SessionLogAdapter(logging.getLogger(name), {"session_id": session_id or "-"})
