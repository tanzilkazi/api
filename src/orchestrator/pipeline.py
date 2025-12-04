# src/orchestrator/pipeline.py

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import List

from src.core.models import Article, ArticleAnalysis,article_from_guardian
from src.llm_client.openai_client import OpenAILLMClient
from src.api_client.base_client import BaseClient
import src.api_client.config as api_config  # whatever you already use there
from src.config import get_env  # your generic get_env helper


def fetch_articles_for_date(client: BaseClient, target_date: date) -> List[Article]:
    """
    Uses your existing BaseClient to fetch Guardian results for a single date,
    and converts them into Article objects.

    IMPORTANT: adjust the call to whatever method you currently have that returns
    the raw Guardian 'results' list.
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


def analyze_articles(articles: List[Article]) -> List[ArticleAnalysis]:
    llm = OpenAILLMClient()
    results: List[ArticleAnalysis] = []

    for a in articles:
        # later you can add try/except here for robustness
        analysis = llm.analyze_article(a)
        results.append(analysis)

    return results


def save_analysis(
    analyses: List[ArticleAnalysis],
    target_date: date,
    out_dir: str = "outputs",
) -> Path:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"guardian_analysis_{target_date.isoformat()}.jsonl"

    with path.open("w", encoding="utf-8") as f:
        for a in analyses:
            f.write(json.dumps(asdict(a)) + "\n")

    return path


def run_pipeline_for_date(target_date: date) -> Path:
    """
    High-level step: fetch → analyse → save.
    """
    api_key = get_env("GUARDIAN_API_KEY", required=True)
    base_url = api_config.BASE_URL  # whatever you used inside BaseClient

    client = BaseClient(base_url=base_url, api_key=api_key)

    articles = fetch_articles_for_date(client, target_date)
    analyses = analyze_articles(articles[0:3])
    out_path = save_analysis(analyses, target_date)

    print(f"Fetched {len(articles)} articles")
    print(f"Wrote {len(analyses)} analyses to {out_path}")
    return out_path


if __name__ == "__main__":
    from datetime import date as _date

    # Default to "yesterday"
    target = _date.today() - timedelta(days=1)
    run_pipeline_for_date(target)
