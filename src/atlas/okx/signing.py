"""OKX API v5 request signing (ISO-8601 timestamp + HMAC-SHA256 + Base64)."""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone


def iso8601_ms(dt: datetime | None = None) -> str:
    """UTC timestamp with millisecond precision, e.g. 2020-12-08T09:08:57.715Z."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ms = int(dt.microsecond / 1000)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def prehash(timestamp: str, method: str, request_path: str, body: str = "") -> str:
    """timestamp + METHOD + requestPath + body (body empty string for GET)."""
    return f"{timestamp}{method.upper()}{request_path}{body or ''}"


def sign_okx_v5(
    timestamp: str,
    method: str,
    request_path: str,
    body: str,
    secret: str,
) -> str:
    """Return Base64 HMAC-SHA256 of the OKX v5 prehash string."""
    msg = prehash(timestamp, method, request_path, body)
    digest = hmac.new(
        secret.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")
