"""Small CLI to run the fetch→analyze→save pipeline for a date.

Usage: `python -m src.cli.run_analysis --date YYYY-MM-DD` (defaults to yesterday).
"""

import argparse
from datetime import datetime, date, timedelta

from src.orchestrator.pipeline import run_pipeline_for_date
from src.config import DEFAULT_ANALYZE_LIMIT


def parse_args() -> argparse.Namespace:
    """
    - function: parse_args
    - logic: Define a minimal CLI that accepts an optional `--date` in
             YYYY-MM-DD format; returns parsed args for the caller.
    """
    parser = argparse.ArgumentParser(description="Fetch & analyse Guardian articles.")
    parser.add_argument(
        "--date",
        help="Date in YYYY-MM-DD format (defaults to yesterday)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_ANALYZE_LIMIT,
        help=f"Number of articles to analyze (default: {DEFAULT_ANALYZE_LIMIT})",
    )
    return parser.parse_args()


def main() -> None:
    """
    - function: main
    - logic: Parse CLI args to determine a target date (defaults to
             yesterday), then call `run_pipeline_for_date` with that date.
    """
    args = parse_args()

    if args.date:
        target_date: date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)

    run_pipeline_for_date(target_date, analyze_limit=args.limit)

if __name__ == "__main__":
    main()
