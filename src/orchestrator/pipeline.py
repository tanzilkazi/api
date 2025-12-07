"""Orchestrator: fetch, analyze, and persist Guardian article analyses.

This module wires together the API client, LLM client and simple
persistence to produce per-day JSONL analysis files in `outputs/`.
Keep this file small: it should orchestrate steps but not implement
low-level API or LLM details.
"""

from __future__ import annotations

import json
import time
import random
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple

from src.core.models import Article, ArticleAnalysis,article_from_guardian
from src.llm_client.gemini_client import GeminiLLMClient
from src.llm_client.base import LLMClient
from src.api_client.base_client import BaseClient
import src.api_client.config as api_config  # whatever you already use there
from src.config import get_env  # your generic get_env helper


def fetch_articles_for_date(client: BaseClient, target_date: date) -> List[Article]:
    """
    - function: fetch_articles_for_date
    - logic: Build Guardian API query params for `target_date`, call the API
             client to retrieve raw results, and convert each raw item to an
             `Article` via `article_from_guardian`.
    """

    date_str = target_date.strftime("%Y-%m-%d")

    params = {
        "from-date": date_str,
        "to-date": date_str,
        "show-fields": "bodyText,headline,publication",
        "order-by": "newest",
        "page-size": 10,
        "page": 1,
    }

    # ⚠️ Replace this with your actual fetch method:
    # e.g. if you built get_all_articles(params) that returns the Guardian results list.
    raw_results = client.get_all_articles(params)  # <-- adjust to your real method

    articles: List[Article] = [article_from_guardian(item) for item in raw_results]
    return articles


def analyze_articles(
    articles: List[Article],
    llm_client: LLMClient | None = None,
    max_retries: int = 3,
    base_backoff: float = 1.0,
    max_backoff: float = 30.0,
) -> Tuple[List[ArticleAnalysis], List[dict]]:
    """
    - function: analyze_articles
    - logic: Use the provided `llm_client` (if given) or instantiate the
             default `GeminiLLMClient`. Analyze each article sequentially and
             return the analyses.
    """
    if llm_client is None:
        llm_client = GeminiLLMClient()

    successes: List[ArticleAnalysis] = []
    failures: List[dict] = []

    for a in articles:
        # later you can add try/except here for robustness
        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                analysis = llm_client.analyze_article(a)
                successes.append(analysis)
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                # If this was the last attempt, record failure context
                if attempt == max_retries:
                    failures.append(
                        {
                            "article_id": getattr(a, "id", None),
                            "title": getattr(a, "title", None),
                            "url": getattr(a, "url", None),
                            "attempts": attempt,
                            "error": repr(e),
                        }
                    )
                else:
                    # compute backoff (honor simple exponential) and add jitter
                    sleep_time = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
                    sleep_time += random.uniform(0, sleep_time * 0.5)
                    # log and sleep before retrying
                    # use print for now; pipeline should use logger in future
                    print(f"LLM call failed for {getattr(a,'id',None)} on attempt {attempt}: {e}; sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)

    return successes, failures


def save_analysis(
    analyses: List[ArticleAnalysis],
    target_date: date,
    out_dir: str = "outputs",
    failures: List[dict] | None = None,
) -> Path:
    """
    - function: save_analysis
    - logic: Ensure the output directory exists and write each successful
             analysis as a JSON line into `guardian_analysis_{date}.jsonl`.
             If `failures` is provided, also write them to
             `guardian_analysis_{date}_failures.jsonl` for later inspection.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    main_path = Path(out_dir) / f"guardian_analysis_{target_date.isoformat()}.jsonl"

    with main_path.open("w", encoding="utf-8") as f:
        for a in analyses:
            f.write(json.dumps(asdict(a)) + "\n")

    if failures:
        fail_path = Path(out_dir) / f"guardian_analysis_{target_date.isoformat()}_failures.jsonl"
        with fail_path.open("w", encoding="utf-8") as ff:
            for item in failures:
                ff.write(json.dumps(item) + "\n")

    return main_path


def run_pipeline_for_date(target_date: date, llm_client: LLMClient | None = None) -> Path:
    """
    High-level step: fetch → analyse → save.
    """
    """
    - function: run_pipeline_for_date
    - logic: Read API configuration from environment, construct a `BaseClient`,
             fetch articles for the date, analyze a (sample) slice, save the
             results and return the output path. Primarily a convenience
             wrapper for running the end-to-end flow.
    """
    api_key = get_env("GUARDIAN_API_KEY", required=True)
    base_url = api_config.BASE_URL  # whatever you used inside BaseClient

    client = BaseClient(base_url=base_url, api_key=api_key)

    articles = fetch_articles_for_date(client, target_date)
    successes, failures = analyze_articles(articles[0:2], llm_client=llm_client)
    out_path = save_analysis(successes, target_date, failures=failures)

    print(f"Fetched {len(articles)} articles")
    print(f"Wrote {len(successes)} analyses to {out_path}")
    if failures:
        print(f"Recorded {len(failures)} failures to outputs/ (see *_failures.jsonl)")
    return out_path


if __name__ == "__main__":
    from datetime import date as _date

    # Default to "yesterday"
    target = _date.today() - timedelta(days=1)
    run_pipeline_for_date(target)
