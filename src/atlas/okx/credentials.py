"""Load OKX EEA API credentials from a JSON file. Never log values."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

log = logging.getLogger("atlas.okx.credentials")

DEFAULT_SECRETS_DIR = Path(
    "/home/box/agent-data/connector-secrets/c6243d50-c126-4d9a-b2c5-7c7c554e4bf5"
)
DEMO_FILENAME = "okx-eea-demo.json"
LIVE_FILENAME = "okx-eea-live.json"
REQUIRED_FIELDS = ("api_key", "api_secret", "passphrase")
SECRETS_PATH_ENV = "ATLAS_OKX_SECRETS_PATH"

Mode = Literal["demo", "live"]


@dataclass(frozen=True)
class OkxCredentials:
    api_key: str
    api_secret: str
    passphrase: str
    source_path: str | None = None

    def __repr__(self) -> str:  # noqa: D105
        return (
            "OkxCredentials(api_key=***, api_secret=***, passphrase=***, "
            f"source_path={self.source_path!r})"
        )

    __str__ = __repr__


def default_secrets_path(mode: Mode) -> Path:
    name = DEMO_FILENAME if mode == "demo" else LIVE_FILENAME
    return DEFAULT_SECRETS_DIR / name


def resolve_secrets_path(mode: Mode, path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    env = os.environ.get(SECRETS_PATH_ENV, "").strip()
    if env:
        return Path(env)
    return default_secrets_path(mode)


def load_okx_credentials(
    mode: Mode,
    path: str | Path | None = None,
) -> OkxCredentials:
    """Load {api_key, api_secret, passphrase} from JSON. Values are never logged."""
    src = resolve_secrets_path(mode, path)
    if not src.is_file():
        raise FileNotFoundError(
            f"OKX secrets file not found for mode={mode!r}: {src}. "
            f"Set {SECRETS_PATH_ENV} or place okx-eea-{mode}.json under {DEFAULT_SECRETS_DIR}."
        )
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"OKX secrets file is not valid JSON: {src}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"OKX secrets file must be a JSON object: {src}")

    missing = [k for k in REQUIRED_FIELDS if not str(raw.get(k) or "").strip()]
    if missing:
        raise ValueError(
            f"OKX secrets file missing required fields {missing} at {src} (values not logged)"
        )

    creds = OkxCredentials(
        api_key=str(raw["api_key"]).strip(),
        api_secret=str(raw["api_secret"]).strip(),
        passphrase=str(raw["passphrase"]).strip(),
        source_path=str(src),
    )
    log.info(
        "loaded OKX credentials mode=%s path=%s fields=%s (values redacted)",
        mode,
        src,
        list(REQUIRED_FIELDS),
    )
    return creds
