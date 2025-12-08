# src/config.py

import logging
import os
from typing import Any

from dotenv import load_dotenv
import requests

load_dotenv()
from src.logging_utils import trace

logger = logging.getLogger(__name__)


@trace
def get_env(name: str, default: str | None = None, required: bool = False) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@trace
def setup_logging(level: int = logging.WARNING) -> None:
    # Accept either numeric level or textual level name (e.g. "DEBUG", "INFO")
    lvl = parse_level(level)

    # Clear existing handlers and configure a single StreamHandler with kv pairs
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    fmt = "ts=%(asctime)s level=%(levelname)s name=%(name)s msg=%(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    root.setLevel(lvl)

    # # Ensure network-related loggers remain at DEBUG level so connection details are visible.
    # for net_logger in ("src.api_client", "requests", "urllib3", "http.client", "urllib3.connectionpool"):
    #     logging.getLogger(net_logger).setLevel(logging.DEBUG)


@trace
def parse_level(lv: Any) -> int:
    """Normalize a level name or number to a logging level integer.

    "TRACE" (if provided) will be treated as INFO to preserve compatibility
    while avoiding a custom logging level.
    """
    if isinstance(lv, int):
        return lv
    name = str(lv).upper()
    if name == "TRACE":
        return logging.INFO
    try:
        return int(name)
    except Exception:
        return getattr(logging, name, logging.WARNING)


@trace
def make_session(user_agent: str = "api-integration-lab/1.0") -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
    )
    return session


# Project-wide defaults (centralized config)
DEFAULT_PAGE_SIZE: int = 10
DEFAULT_OUTPUT_DIR: str = "outputs"
# Number of articles to analyze by default (sample size)
DEFAULT_ANALYZE_LIMIT: int = 2
# Retry/backoff defaults used by HTTP/LLM code when not overridden
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_BASE_BACKOFF: float = 1.0
DEFAULT_MAX_BACKOFF: float = 30.0
