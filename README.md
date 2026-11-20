# Benford's Law — Web Data Tester

A small Python app that scrapes a curated list of public web pages rich in real-world numbers, extracts first significant digits, and compares the distribution to [Benford's law](https://en.wikipedia.org/wiki/Benford%27s_law).

## Features

- **100 editable targets** in `config/sites.json` (statistics agencies, Wikipedia tables, sports/finance pages, etc.)
- Polite scraping: custom User-Agent, timeouts, limited concurrency, `robots.txt` checks
- Number parsing for US/EU thousands separators, decimals, negatives, `%`, and common currency symbols
- Optional filtering of years 1900–2099
- Chi-square and mean absolute deviation (MAD) vs Benford expected `log10(1 + 1/d)`
- **Streamlit UI**: overall histogram, per-site table, re-run button
- Artifacts: `output/benford_histogram.png`, `output/site_results.csv`, `output/run_summary_latest.json`

## Requirements

- Python 3.10+
- macOS / Linux / Windows

## Quick start (one command)

With [uv](https://github.com/astral-sh/uv) (recommended on macOS):

```bash
chmod +x run.sh && ./run.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py --server.port 43123
```

Open **http://127.0.0.1:43123**, then click **Run scrape & analysis** in the sidebar. The first run fetches all configured sites and may take several minutes.

### Headless run (no UI)

```bash
source .venv/bin/activate
python -m benford.cli
```

## Configuration

Edit `config/sites.json` to add or remove targets:

```json
{
  "sites": [
    {"name": "Example stats page", "url": "https://example.gov/statistics"}
  ]
}
```

## Tests

```bash
pytest -q
```

## Ethics / robots

This tool is for education and research. It identifies itself in the User-Agent, honors `robots.txt`, uses modest concurrency, and skips disallowed URLs. Do not use it against sites that prohibit automated access or require login.

## License

MIT