"""Streamlit UI for Benford's law web data analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from benford.runner import OUTPUT_DIR, run_analysis
from benford.stats import BENFORD_EXPECTED

DEFAULT_SITES = Path(__file__).resolve().parent / "config" / "sites.json"


st.set_page_config(page_title="Benford's Law — Web Data", layout="wide")
st.title("Benford's Law on real-world web data")
st.caption(
    "Fetches public pages, extracts numbers, compares first-digit frequencies to Benford's law."
)

with st.sidebar:
    sites_path = st.text_input("Sites config", value=str(DEFAULT_SITES))
    ignore_years = st.checkbox("Ignore years 1900–2099", value=True)
    concurrency = st.slider("Max concurrent requests", 1, 10, 5)
    run_btn = st.button("Run scrape & analysis", type="primary")

if "payload" not in st.session_state:
    st.session_state.payload = None

if run_btn:
    with st.spinner("Fetching sites and extracting digits (this may take several minutes)…"):
        try:
            st.session_state.payload = run_analysis(
                Path(sites_path),
                ignore_years=ignore_years,
                output_dir=OUTPUT_DIR,
                max_concurrency=concurrency,
            )
        except Exception as e:
            st.error(f"Run failed: {e}")
            st.session_state.payload = None

payload = st.session_state.payload

if payload is None:
    st.info("Click **Run scrape & analysis** in the sidebar to start.")
    if (OUTPUT_DIR / "run_summary_latest.json").exists():
        if st.button("Load last saved results"):
            import json

            st.session_state.payload = json.loads(
                (OUTPUT_DIR / "run_summary_latest.json").read_text(encoding="utf-8")
            )
            st.rerun()
    st.stop()

overall = payload["overall"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Sites OK", payload["sites_ok"], delta=None)
col2.metric("Sites failed / blocked", payload["sites_failed"])
col3.metric("Digits collected", payload["total_digits"])
col4.metric("MAD vs Benford", f"{overall['mad']:.4f}")

st.subheader("Observed vs expected (overall)")
hist_path = Path(payload["artifacts"]["histogram_png"])
if hist_path.is_file():
    st.image(str(hist_path), use_container_width=True)
else:
    counts = overall["counts"]
    import matplotlib.pyplot as plt

    digits = list(range(1, 10))
    total = sum(counts.values())
    obs = [counts.get(d, 0) / total if total else 0 for d in digits]
    exp = [BENFORD_EXPECTED[d] for d in digits]
    fig, ax = plt.subplots()
    x = range(9)
    w = 0.35
    ax.bar([i - w / 2 for i in x], obs, w, label="Observed")
    ax.bar([i + w / 2 for i in x], exp, w, label="Benford")
    ax.set_xticks(list(x))
    ax.set_xticklabels(digits)
    ax.legend()
    st.pyplot(fig)

st.write(
    f"Chi-square (df=8): **{overall['chi_square']:.2f}** — lower values (relative to critical table) "
    "suggest closer fit; interpret with sample size in mind."
)

st.subheader("Per-site results")
df = pd.DataFrame(payload["sites"])
df = df.sort_values(by=["ok", "n_digits"], ascending=[True, False])
st.dataframe(
    df[["name", "status", "n_digits", "chi_square", "mad", "error", "url"]],
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download site CSV",
    data=Path(payload["artifacts"]["site_csv"]).read_bytes(),
    file_name="site_results.csv",
    mime="text/csv",
)