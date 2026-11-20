"""CLI entry point for headless runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from benford.runner import run_analysis


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    default_sites = root / "config" / "sites.json"
    p = argparse.ArgumentParser(description="Run Benford web scrape (headless)")
    p.add_argument("--sites", type=Path, default=default_sites)
    p.add_argument("--no-ignore-years", action="store_true")
    p.add_argument("--concurrency", type=int, default=5)
    args = p.parse_args()
    summary = run_analysis(
        args.sites,
        ignore_years=not args.no_ignore_years,
        max_concurrency=args.concurrency,
    )
    print(
        f"Done: {summary['sites_ok']}/{summary['sites_attempted']} sites OK, "
        f"{summary['total_digits']} digits, histogram at {summary['artifacts']['histogram_png']}"
    )


if __name__ == "__main__":
    main()