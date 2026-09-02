"""Structured logging without secrets."""

from __future__ import annotations

import logging
import sys


_SECRET_FRAGMENTS = (
    "api_key",
    "api_secret",
    "passphrase",
    "private_key",
    "secret_key",
    "authorization",
)


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage()).lower()
        for frag in _SECRET_FRAGMENTS:
            if frag in msg and ("=" in msg or ":" in msg):
                record.msg = "[REDACTED — possible secret in log message]"
                record.args = ()
                break
        return True


def setup_logging(level: str = "INFO") -> logging.Logger:
    root = logging.getLogger("atlas")
    if root.handlers:
        root.setLevel(level.upper())
        return root
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)sZ %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    handler.addFilter(_RedactFilter())
    # Force UTC in asctime
    logging.Formatter.converter = __import__("time").gmtime  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(level.upper())
    root.propagate = False
    return root
