"""Small CLI to run the fetch→analyze→save pipeline for a date.

Usage: `python -m src.cli.run_analysis --date YYYY-MM-DD` (defaults to yesterday).
"""

import argparse
import logging
from datetime import datetime, date, timedelta

from src.orchestrator.pipeline import run_pipeline_for_date
from src.config import DEFAULT_ANALYZE_LIMIT, setup_logging, parse_level
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
        help="Enable function entry/exit tracing (emitted at INFO level when enabled)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Enable human-readable status updates during pipeline execution",
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
    requested_level = getattr(args, "log_level", "WARNING")
    # If tracing requested, ensure the root level is at least INFO so
    # trace decorator messages (at INFO) can be emitted.
    if getattr(args, "trace", False):
        try:
            lvl_val = parse_level(requested_level)
        except Exception:
            lvl_val = logging.WARNING
        if lvl_val > logging.INFO:
            requested_level = "INFO"

    setup_logging(requested_level, trace=getattr(args, "trace", False))

    if args.date:
        target_date: date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)

    run_pipeline_for_date(target_date, analyze_limit=args.limit, status=getattr(args, "status", False))

if __name__ == "__main__":
    main()
