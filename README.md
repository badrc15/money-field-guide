# Money Field Guide

A beginner-friendly finance guide built with Python, FastAPI, SQLite, and plain JavaScript. It covers investing basics, shares and funds, bonds, UK ISAs, research habits, finance careers, a live market scout, and a daily reading list.

## Local run

Use Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs>. Set `DATABASE_PATH` to move the local SQLite lesson journal (default `money_field_guide.db`). Market and news feeds need outbound internet access; if a provider is unavailable, the page explains that and links to source websites instead of making up data.

## Learn the Python

1. **Data and calculations — `main.py`:** `yahoo_stock` derives a recent price change and observed high-low range from daily bars. `risk_label` maps the range into plain-language teaching bands.
2. **Fetching and freshness — `main.py`:** `scout_data` requests public crypto and stock data, sorts by the measured recent move, and caches a successful scan for a day. The refresh button bypasses that cache. `news_data` reads publisher RSS headlines and caches them for an hour.
3. **API and browser — `main.py`, `static/app.js`:** FastAPI returns JSON. JavaScript renders the timestamp, source, market window, recent move, volatility cue, and linked headlines.

## Data and limitations

- Crypto prices and metadata come from CoinGecko's public market endpoint. Stock bars use Yahoo Finance's chart endpoint. Availability, terms, rate limits, delays, coverage, currencies, and methodology are controlled by those providers; the stock endpoint is not an official Yahoo developer API.
- The scan covers CoinGecko's top 60 by market capitalization and a fixed set of eight large US stocks. It is not a broad universe search and can miss smaller, newer, or non-US assets.
- “Recent swing” is high-to-low movement over 24 hours for crypto and the latest daily session for stocks. The cutoffs (under 3%, 3–8%, 8% or more) are simple teaching labels, not a full volatility model, suitability assessment, or judgement that an asset is a good/bad investment. The market change windows also differ (7 calendar days vs 5 sessions).
- The scout ranks recent historical change. Momentum can reverse and is not evidence that an asset will make a large future move. It does not generate buy or sell recommendations.
- The daily list uses attributed CoinDesk and BBC Business RSS headlines. On GitHub Pages, a scheduled GitHub Actions build refreshes the static headline snapshot about hourly. Review RSS terms and obtain any needed permissions before operating a public or commercial service.
- The editorial guide is general learning material, not personalized financial, investment, tax, or legal advice. Its UK ISA examples have dates and official links because rules can change. Verify current rules before acting.

## GitHub Pages deployment

The GitHub Actions workflow in `.github/workflows/pages.yml` publishes the HTML, CSS, and JavaScript on pushes to `main` and refreshes the static market/news snapshots hourly. GitHub Pages serves the site from the project repository at <https://badrc15.github.io/money-field-guide/>.

For the first deployment, open **Settings → Pages** in this repository and set **Build and deployment → Source** to **GitHub Actions**. After that, the workflow deploys updates automatically. Scheduled refreshes depend on GitHub Actions availability and market/news provider limits.

GitHub Pages cannot run Python, so the hosted scout and headlines use JSON snapshots generated during each Pages build. For a local version with on-demand API refreshes, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

The live scout and headlines depend on third-party providers and can be delayed or unavailable. Review provider terms and rate limits before running the app as a commercial service.
