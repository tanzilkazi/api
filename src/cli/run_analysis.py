# cli/run_analysis.py

import argparse
from datetime import datetime, date, timedelta

from src.orchestrator.pipeline import run_pipeline_for_date


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch & analyse Guardian articles.")
    parser.add_argument(
        "--date",
        help="Date in YYYY-MM-DD format (defaults to yesterday)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.date:
        target_date: date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)

    run_pipeline_for_date(target_date)


if __name__ == "__main__":
    main()
