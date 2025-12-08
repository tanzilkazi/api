"""Logging helpers: trace decorator and safe repr for logging.

Provides a `trace` decorator which logs function entry/exit when TRACE
level is enabled. Also contains a small `safe_repr` helper that redacts
likely secrets from dictionaries and limits length of representations.
"""
from __future__ import annotations

import functools
import logging
import time
from typing import Any


_REDACT_KEYS = ("key", "token", "secret", "password", "api")


def _should_redact(k: str) -> bool:
    lo = k.lower()
    return any(p in lo for p in _REDACT_KEYS)


def safe_repr(obj: Any, max_len: int = 300) -> str:
    """Return a short, safe string representation of `obj` suitable for logs.

    - Redacts values for dict keys that look like secrets.
    - Truncates long strings.
    """
    try:
        if isinstance(obj, dict):
            parts = []
            for k, v in obj.items():
                if isinstance(k, str) and _should_redact(k):
                    parts.append(f"{k}=<REDACTED>")
                else:
                    parts.append(f"{k}={safe_repr(v, max_len=80)}")
            s = "{" + ", ".join(parts) + "}"
        elif isinstance(obj, (list, tuple)):
            inner = ", ".join(safe_repr(x, max_len=80) for x in list(obj)[:10])
            s = ("[" + inner + "]") if isinstance(obj, list) else ("(" + inner + ")")
        elif isinstance(obj, str):
            if len(obj) > max_len:
                s = obj[: max_len - 3] + "..."
            else:
                s = obj
        else:
            s = repr(obj)
    except Exception:
        s = "<unrepresentable>"

    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def trace(fn):
    """Decorator that logs function entry and exit at INFO level.

    Tracing is emitted at INFO; to enable use `--trace` which sets the
    global level to INFO, or set the logger level accordingly.
    """

    @functools.wraps(fn)
    def _wrapped(*args, **kwargs):
        logger = logging.getLogger(fn.__module__)
        # Trace is emitted at DEBUG level per user request.
        if not logger.isEnabledFor(logging.DEBUG):
            return fn(*args, **kwargs)

        logger.debug("enter=%s args=%s kwargs=%s", fn.__qualname__, safe_repr(args, 200), safe_repr(kwargs, 200))
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            dt = time.perf_counter() - t0
            logger.debug("exit=%s duration=%.6fs", fn.__qualname__, dt)

    return _wrapped
