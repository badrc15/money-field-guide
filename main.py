"""Money Field Guide: a beginner's finance learning app.

Python lesson: small functions calculate observable market signals; routes expose
them as JSON. This is research practice, not a trading recommendation service.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import os
import sqlite3
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "money_field_guide.db"))
CACHE: dict[str, tuple[float, dict]] = {}
CRYPTO_FEED = "https://www.coindesk.com/arc/outboundfeeds/rss/"
BUSINESS_FEED = "https://feeds.bbci.co.uk/news/business/rss.xml"
STOCKS = [("NVDA", "NVIDIA"), ("MSFT", "Microsoft"), ("AMZN", "Amazon"),
          ("GOOGL", "Alphabet"), ("META", "Meta"), ("TSLA", "Tesla"),
          ("AVGO", "Broadcom"), ("AMD", "AMD")]

def initialize_database():
    """Create a small local table ready to store lesson progress."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS lesson_progress (
            lesson_id TEXT PRIMARY KEY, completed_at TEXT
        )""")

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield

app = FastAPI(title="Money Field Guide", description="A beginner's finance learning guide.", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "MoneyFieldGuide/1.0 (educational; contact: local app)", "Accept": "application/json"})
    with urlopen(request, timeout=4) as response:
        return json.loads(response.read())

def yahoo_stock(symbol: str, name: str) -> dict:
    """Read the latest 5 daily bars from Yahoo's chart endpoint."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?range=5d&interval=1d"
    payload = get_json(url)["chart"]["result"][0]
    quote = payload["indicators"]["quote"][0]
    closes = [v for v in quote.get("close", []) if v is not None]
    highs = [v for v in quote.get("high", []) if v is not None]
    lows = [v for v in quote.get("low", []) if v is not None]
    if len(closes) < 2:
        raise ValueError("Not enough recent stock bars")
    swing = ((max(highs[-1:], default=closes[-1]) - min(lows[-1:], default=closes[-1])) / closes[-1]) * 100
    change = ((closes[-1] / closes[0]) - 1) * 100
    updated = datetime.fromtimestamp(payload["meta"]["regularMarketTime"], timezone.utc).isoformat()
    return {"symbol": symbol, "name": name, "kind": "Stock", "price": closes[-1],
            "currency": payload["meta"].get("currency", "USD"), "change": round(change, 2),
            "change_window": "5 sessions", "observed_range": round(swing, 2), "range_window": "latest session",
            "source": "Yahoo Finance chart data", "updated_at": updated,
            "source_url": "https://finance.yahoo.com/quote/" + symbol}

def risk_label(range_percent: float) -> str:
    if range_percent >= 8:
        return "High recent swing"
    if range_percent >= 3:
        return "Elevated recent swing"
    return "Lower recent swing"

def scout_data() -> dict:
    """Scan a bounded sample universe and report recent movement, not predictions."""
    now = time.time()
    cached = CACHE.get("scout")
    if cached and now - cached[0] < 86400:
        return cached[1]
    assets: list[dict] = []
    errors: list[str] = []
    try:
        query = urlencode({"vs_currency": "gbp", "order": "market_cap_desc", "per_page": "60",
                           "page": "1", "sparkline": "false", "price_change_percentage": "7d"})
        coins = get_json("https://api.coingecko.com/api/v3/coins/markets?" + query)
        for coin in coins:
            change = coin.get("price_change_percentage_7d_in_currency")
            high, low, price = coin.get("high_24h"), coin.get("low_24h"), coin.get("current_price")
            if change is None or not price or not high or not low:
                continue
            assets.append({"symbol": coin["symbol"].upper(), "name": coin["name"], "kind": "Crypto",
                "price": price, "currency": "GBP", "change": round(change, 2), "change_window": "7 days",
                "observed_range": round((high-low)/price*100, 2), "range_window": "24 hours",
                "market_cap": coin.get("market_cap"), "volume": coin.get("total_volume"),
                "source": "CoinGecko", "updated_at": coin.get("last_updated"),
                "source_url": "https://www.coingecko.com/en/coins/" + coin["id"]})
    except Exception as error:
        errors.append("Crypto market data is temporarily unavailable (" + type(error).__name__ + ").")
    def fetch_stock(item):
        try:
            return yahoo_stock(*item)
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        stock_results = list(pool.map(fetch_stock, STOCKS))
    available_stocks = [asset for asset in stock_results if asset]
    assets.extend(available_stocks)
    if not available_stocks:
        errors.append("Stock market data is temporarily unavailable.")
    for asset in assets:
        asset["risk_label"] = risk_label(asset["observed_range"])
    assets.sort(key=lambda item: item["change"], reverse=True)
    payload = {"assets": assets, "updated_at": datetime.now(timezone.utc).isoformat(),
        "source_note": "Crypto: change over 7 days, range over 24 hours. Stocks: change and range over the last 5 trading sessions / latest session. Different markets and time windows are not directly comparable.",
        "universe_note": "This is a limited data scan of larger crypto assets and a fixed set of US large-cap stocks. It does not cover every market or identify future winners.",
        "errors": errors, "is_live": bool(assets)}
    CACHE["scout"] = (now, payload)
    return payload

@app.get("/api/scout")
def get_scout(refresh: bool = False):
    if refresh:
        CACHE.pop("scout", None)
    return scout_data()

def read_feed(url: str, label: str, kind: str) -> list[dict]:
    request = Request(url, headers={"User-Agent": "MoneyFieldGuide/1.0 (educational)", "Accept": "application/rss+xml, application/atom+xml, application/xml"})
    with urlopen(request, timeout=5) as response:
        root = ET.fromstring(response.read())
    entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    stories = []
    for entry in entries[:8]:
        def get_text(name):
            element = entry.find(name)
            if element is None:
                element = entry.find("{http://www.w3.org/2005/Atom}" + name)
            return (element.text or "").strip() if element is not None else ""
        link = get_text("link")
        if not link:
            link_element = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_element.get("href", "") if link_element is not None else ""
        stories.append({"title": get_text("title"), "link": link, "published": get_text("pubDate") or get_text("updated"),
                        "source": label, "kind": kind})
    return stories

def news_data() -> dict:
    now = time.time()
    cached = CACHE.get("news")
    if cached and now - cached[0] < 3600:
        return cached[1]
    stories, sources = [], []
    for url, label, kind in [(BUSINESS_FEED, "BBC News · Business", "Markets & business"),
                             (CRYPTO_FEED, "CoinDesk", "Digital assets")]:
        try:
            stories.extend(read_feed(url, label, kind))
            sources.append(label)
        except Exception:
            continue
    def published_time(story):
        try:
            return parsedate_to_datetime(story["published"]).timestamp()
        except (TypeError, ValueError, OverflowError):
            try:
                return datetime.fromisoformat(story["published"].replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError, OverflowError):
                return 0
    stories.sort(key=published_time, reverse=True)
    payload = {"stories": stories[:12], "updated_at": datetime.now(timezone.utc).isoformat(),
               "sources": sources, "available": bool(stories),
               "message": "Fresh publisher RSS headlines, refreshed hourly when the app is open." if stories else "Live headlines could not be reached. Use the publisher links below to read current coverage."}
    CACHE["news"] = (now, payload)
    return payload

@app.get("/api/news")
def get_news(refresh: bool = False):
    if refresh:
        CACHE.pop("news", None)
    return news_data()
