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
- The daily list fetches CoinDesk and BBC Business RSS on page load, caches for one hour, and refreshes while the page remains open. It does not run a background scheduler while nobody is using the app. It shows attributed headlines linking to the publishers. Review RSS terms and obtain any needed permissions before operating a public or commercial service.
- The editorial guide is general learning material, not personalized financial, investment, tax, or legal advice. Its UK ISA examples have dates and official links because rules can change. Verify current rules before acting.

## Deployment configuration

The included `Dockerfile` reads the hosting platform's `PORT` and stores SQLite at `/data/money_field_guide.db`. `render.yaml` describes a Render Docker service with a persistent disk.

```bash
docker build -t money-field-guide .
docker run --rm -p 8000:8000 -v money-field-data:/data money-field-guide
```

This project is not deployed or published. Public deployment will require reviewing third-party market-data and RSS terms, uptime, rate limits, and privacy needs.
