"""Small CLI to run the fetch→analyze→save pipeline for a date.

Usage: `python -m src.cli.run_analysis --date YYYY-MM-DD` (defaults to yesterday).
"""

import argparse
import logging
from datetime import datetime, date, timedelta

from src.orchestrator.pipeline import run_pipeline_for_date
from src.config import DEFAULT_ANALYZE_LIMIT, setup_logging
from src.logging_utils import trace

logger = logging.getLogger(__name__)


@trace
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
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        help="Logging level name or numeric value (e.g. DEBUG, INFO, WARNING)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable function entry/exit tracing (emitted at INFO level)",
    )
    return parser.parse_args()


@trace
def main() -> None:
    """
    - function: main
    - logic: Parse CLI args to determine a target date (defaults to
             yesterday), then call `run_pipeline_for_date` with that date.
    """
    args = parse_args()

    # Configure logging early so modules can emit logs.
    # If --trace is requested we map it to INFO-level tracing.
    requested_level = "INFO" if getattr(args, "trace", False) else getattr(args, "log_level", "WARNING")
    setup_logging(requested_level)

    if args.date:
        target_date: date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)

    run_pipeline_for_date(target_date, analyze_limit=args.limit)

if __name__ == "__main__":
    main()
