# src/clients/guardian_client.py

#!/usr/bin/env python3
"""
Guardian API client — based on guardian_starter.py

- Uses GUARDIAN_API_KEY from environment (.env)
- Provides GuardianClient with:
  - search()
  - search_all()
- Handles:
  - Auth errors
  - Rate limiting with backoff+jitter
  - Server errors
  
- Usage:
python3 -m src.clients.guardian_starter --q "Australia" --page-size 5
"""

import argparse
import json
import logging
import time
import random
from typing import Dict, Any, Generator, Optional, List

import requests

from src.config import get_env, make_session, setup_logging

BASE_URL = "https://content.guardianapis.com"
DEFAULT_TIMEOUT = 20  # seconds
LOGGER = logging.getLogger("guardian")


class GuardianError(Exception):
    """Base class for Guardian client errors."""


class GuardianAuthError(GuardianError):
    """401/403 auth/permission errors."""


class GuardianRateLimit(GuardianError):
    """429 rate limit errors."""


class GuardianServerError(GuardianError):
    """5xx upstream errors."""


class GuardianClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        backoff_base: float = 1.0,
    ) -> None:
        self.api_key = api_key or get_env("GUARDIAN_API_KEY", required=True)
        self.session = session or make_session(user_agent="guardian-starter/1.0")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def _sleep_with_jitter(self, attempt: int, from_rate_limit: bool = False) -> None:
        base = self.backoff_base * (2 ** (attempt - 1))
        jitter = random.random() * 0.3
        wait = base + jitter
        if from_rate_limit:
            wait += 0.5
        LOGGER.warning("Retrying in %.2fs (attempt %d)...", wait, attempt)
        time.sleep(wait)

    def _request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params or {})
        params.setdefault("api-key", self.api_key)

        url = f"{BASE_URL}{path}"
        attempt = 0

        while True:
            attempt += 1
            start = time.time()
            try:
                resp = self.session.request(method, url, params=params, timeout=self.timeout)
            except requests.RequestException as e:
                if attempt > self.max_retries:
                    raise GuardianError(f"Network error after retries: {e!r}")
                self._sleep_with_jitter(attempt)
                continue

            elapsed = (time.time() - start) * 1000
            LOGGER.debug("HTTP %s %s %s %.1fms", method, path, resp.status_code, elapsed)

            if resp.status_code in (401, 403):
                raise GuardianAuthError(f"Auth error {resp.status_code}: {resp.text[:200]}")
            if resp.status_code == 429:
                if attempt > self.max_retries:
                    raise GuardianRateLimit(f"Rate limited after retries: {resp.text[:200]}")
                self._sleep_with_jitter(attempt, from_rate_limit=True)
                continue
            if 500 <= resp.status_code < 600:
                if attempt > self.max_retries:
                    raise GuardianServerError(f"Server error {resp.status_code}: {resp.text[:200]}")
                self._sleep_with_jitter(attempt)
                continue
            if not resp.ok:
                raise GuardianError(f"HTTP {resp.status_code}: {resp.text[:200]}")

            try:
                data = resp.json()
            except json.JSONDecodeError:
                raise GuardianError("Non-JSON response from API.")

            if "response" not in data:
                raise GuardianError("Malformed response: missing 'response'")
            return data["response"]

    # search() and search_all() stay exactly like your original file

    def search(
        self,
        q: str,
        page_size: int = 20,
        page: int = 1,
        show_fields: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: Optional[str] = None,
        section: Optional[str] = None,
        tag: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "q": q,
            "page-size": page_size,
            "page": page,
        }
        if show_fields:
            params["show-fields"] = show_fields
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        if order_by:
            params["order-by"] = order_by
        if section:
            params["section"] = section
        if tag:
            params["tag"] = tag
        if additional_params:
            params.update(additional_params)

        return self._request("GET", "/search", params)

    def search_all(
        self,
        q: str,
        total_items: int = 100,
        page_size: int = 20,
        show_fields: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: Optional[str] = None,
        section: Optional[str] = None,
        tag: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        fetched = 0
        page = 1
        while fetched < total_items:
            resp = self.search(
                q=q,
                page_size=page_size,
                page=page,
                show_fields=show_fields,
                from_date=from_date,
                to_date=to_date,
                order_by=order_by,
                section=section,
                tag=tag,
                additional_params=additional_params,
            )
            results: List[Dict[str, Any]] = resp.get("results", [])
            if not results:
                break
            for item in results:
                yield item
                fetched += 1
                if fetched >= total_items:
                    break
            current_page = resp.get("currentPage", page)
            pages = resp.get("pages", current_page)
            if current_page >= pages:
                break
            page = current_page + 1


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Guardian API starter CLI")
    p.add_argument("--q", default="Australia", help="Query string")
    p.add_argument("--page-size", type=int, default=10, help="Items per page")
    p.add_argument("--pages", type=int, default=1, help="How many pages to fetch")
    p.add_argument("--show-fields", default="headline,trailText,byline", help="CSV list of fields")
    p.add_argument("--from-date", help="YYYY-MM-DD")
    p.add_argument("--to-date", help="YYYY-MM-DD")
    p.add_argument("--order-by", choices=["newest", "oldest", "relevance"])
    p.add_argument("--section", help="Filter by section id")
    p.add_argument("--tag", help="Filter by tag id")
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    client = GuardianClient()
    total = args.page_size * max(1, args.pages)

    LOGGER.info("Searching: q=%r, total≈%d, fields=%s", args.q, total, args.show_fields)

    count = 0
    for item in client.search_all(
        q=args.q,
        total_items=total,
        page_size=args.page_size,
        show_fields=args.show_fields,
        from_date=args.from_date,
        to_date=args.to_date,
        order_by=args.order_by,
        section=args.section,
        tag=args.tag,
    ):
        print(json.dumps(item, indent=2))
        count += 1

    LOGGER.info("Done. Printed %d items.", count)


if __name__ == "__main__":
    main()
