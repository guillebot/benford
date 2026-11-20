"""Orchestrate scraping, analysis, and artifact export."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from benford.extract import ExtractOptions, leading_digits_from_text
from benford.scraper import fetch_all_sites
from benford.stats import BENFORD_EXPECTED, fit_summary

OUTPUT_DIR = Path("output")


def load_sites(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("sites", [])


def save_histogram(overall_counts: dict[int, int], out_path: Path) -> None:
    digits = list(range(1, 10))
    obs_total = sum(overall_counts.values())
    observed = [overall_counts.get(d, 0) / obs_total if obs_total else 0 for d in digits]
    expected = [BENFORD_EXPECTED[d] for d in digits]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(digits))
    width = 0.35
    ax.bar([i - width / 2 for i in x], observed, width, label="Observed", color="#2563eb")
    ax.bar([i + width / 2 for i in x], expected, width, label="Benford expected", color="#94a3b8")
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(d) for d in digits])
    ax.set_xlabel("First significant digit")
    ax.set_ylabel("Proportion")
    ax.set_title("Observed vs Benford's law (all sites)")
    ax.legend()
    ax.set_ylim(0, max(max(observed), max(expected)) * 1.15)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run_analysis(
    sites_path: Path,
    *,
    ignore_years: bool = True,
    output_dir: Path | None = None,
    max_concurrency: int = 5,
) -> dict:
    output_dir = output_dir or OUTPUT_DIR
    sites = load_sites(sites_path)
    opts = ExtractOptions(ignore_years=ignore_years)
    results = asyncio.run(fetch_all_sites(sites, max_concurrency=max_concurrency))

    site_rows: list[dict] = []
    all_digits: list[int] = []
    overall_counts = {d: 0 for d in range(1, 10)}

    for fr in results:
        row: dict = {
            "name": fr.name,
            "url": fr.url,
            "status": fr.status,
            "ok": fr.ok,
            "http_status": fr.http_status,
            "error": fr.error,
            "n_numbers": 0,
            "n_digits": 0,
            "chi_square": None,
            "mad": None,
        }
        if fr.ok and fr.text:
            digits = leading_digits_from_text(fr.text, opts)
            summary = fit_summary(digits)
            row["n_digits"] = summary["n_digits"]
            row["chi_square"] = summary["chi_square"]
            row["mad"] = summary["mad"]
            all_digits.extend(digits)
            for d, c in summary["counts"].items():
                overall_counts[d] += c
        site_rows.append(row)

    overall = fit_summary(all_digits)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "benford_histogram.png"
    save_histogram(overall_counts, png_path)

    csv_path = output_dir / "site_results.csv"
    pd.DataFrame(site_rows).to_csv(csv_path, index=False)

    json_path = output_dir / f"run_summary_{ts}.json"
    payload = {
        "generated_at": ts,
        "sites_config": str(sites_path),
        "sites_attempted": len(sites),
        "sites_ok": sum(1 for r in site_rows if r["ok"]),
        "sites_failed": sum(1 for r in site_rows if not r["ok"]),
        "total_digits": overall["n_digits"],
        "ignore_years": ignore_years,
        "overall": {
            "counts": overall["counts"],
            "proportions": overall["proportions"],
            "chi_square": overall["chi_square"],
            "mad": overall["mad"],
        },
        "sites": site_rows,
        "artifacts": {
            "histogram_png": str(png_path),
            "site_csv": str(csv_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_json = output_dir / "run_summary_latest.json"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload