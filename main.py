import os
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import httpx


# Kalshi public market data — no auth required for read-only
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=15.0)
    yield
    await http_client.aclose()


app = FastAPI(title="Kalshi Wrapper", lifespan=lifespan)


HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kalshi Prediction Markets</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  background:#0a0a0a;
  color:#e8e8e8;
  font-family:system-ui,-apple-system,sans-serif;
  padding:40px 20px;
  line-height:1.5;
}
.container{
  max-width:640px;
  margin:0 auto;
  animation:fadeIn 0.6s ease-out;
}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:12px;
}
h1{
  font-family:monospace;
  font-size:28px;
  color:#3498DB;
  font-weight:700;
}
.health{
  font-family:monospace;
  font-size:13px;
  color:#555;
  display:flex;
  align-items:center;
  gap:6px;
}
.health .d{
  width:8px;
  height:8px;
  border-radius:50%;
  background:#555;
  transition:background .3s;
}
.health .d.on{
  background:#4CAF50;
}
.subtitle{
  color:#888;
  font-size:14px;
  margin-bottom:32px;
}
.card{
  background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.07);
  border-radius:16px;
  padding:24px;
  margin-bottom:24px;
}
.section-title{
  font-size:11px;
  letter-spacing:1px;
  text-transform:uppercase;
  color:#666;
  font-weight:600;
  margin-bottom:16px;
}
.market-card{
  background:rgba(255,255,255,.02);
  border:1px solid rgba(255,255,255,.05);
  border-radius:12px;
  padding:16px;
  margin-bottom:12px;
  transition:all 0.2s ease;
}
.market-card:hover{
  background:rgba(255,255,255,.04);
  border-color:rgba(52,152,219,.3);
}
.market-title{
  font-size:14px;
  font-weight:500;
  margin-bottom:12px;
  color:#e8e8e8;
  line-height:1.4;
}
.prob-bar-container{
  background:rgba(255,255,255,.05);
  height:24px;
  border-radius:6px;
  overflow:hidden;
  position:relative;
  margin-bottom:8px;
}
.prob-bar-fill{
  background:linear-gradient(90deg, #3498DB, #2980B9);
  height:100%;
  transition:width 0.5s ease;
  display:flex;
  align-items:center;
  justify-content:flex-end;
  padding-right:8px;
}
.prob-bar-pct{
  color:#fff;
  font-size:11px;
  font-weight:600;
  font-family:monospace;
}
.price-text{
  font-family:monospace;
  font-size:12px;
  color:#999;
  margin-bottom:4px;
}
.volume-text{
  font-size:11px;
  color:#666;
}
.category-tags{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:24px;
}
.tag{
  background:rgba(255,255,255,.05);
  color:#888;
  padding:6px 12px;
  border-radius:12px;
  font-size:11px;
  border:1px solid rgba(255,255,255,.08);
}
.search-form{
  display:flex;
  gap:8px;
  margin-bottom:12px;
}
.search-input{
  flex:1;
  background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.1);
  border-radius:12px;
  padding:12px 16px;
  color:#e8e8e8;
  font-size:14px;
  outline:none;
  transition:all 0.2s;
}
.search-input:focus{
  border-color:#3498DB;
  background:rgba(255,255,255,.08);
}
.search-btn{
  background:#3498DB;
  color:#fff;
  border:none;
  border-radius:12px;
  padding:12px 24px;
  font-size:14px;
  font-weight:600;
  cursor:pointer;
  transition:all 0.2s;
}
.search-btn:hover{
  background:#2980B9;
  transform:translateY(-1px);
}
.try-section{
  font-size:12px;
  color:#666;
}
.try-section a{
  color:#3498DB;
  text-decoration:none;
  margin-left:4px;
}
.try-section a:hover{
  text-decoration:underline;
}
.loading{
  text-align:center;
  color:#666;
  padding:20px;
}
.error{
  color:#e74c3c;
  background:rgba(231,76,60,.1);
  padding:12px;
  border-radius:8px;
  font-size:13px;
}
.empty{
  text-align:center;
  color:#666;
  padding:20px;
  font-size:13px;
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Kalshi</h1>
    <div class="health"><span class="d" id="dot"></span><span id="health-text">connecting...</span></div>
  </div>
  <div class="subtitle">Prediction markets \\u2014 economics, politics, climate, tech</div>

  <div class="card">
    <div class="section-title">Active Markets</div>
    <div id="markets-container" class="loading">Loading markets...</div>
  </div>

  <div class="category-tags">
    <span class="tag">Economics</span>
    <span class="tag">Politics</span>
    <span class="tag">Climate</span>
    <span class="tag">Tech</span>
    <span class="tag">Science</span>
  </div>

  <div class="card">
    <form class="search-form" onsubmit="handleSearch(event)">
      <input type="text" class="search-input" id="search-input" placeholder="Fed rate" autocomplete="off">
      <button type="submit" class="search-btn">\\u2192 search</button>
    </form>
    <div class="try-section">
      Try:
      <a href="#" onclick="quickSearch('GDP');return false">GDP</a> \\u00B7
      <a href="#" onclick="quickSearch('inflation');return false">inflation</a> \\u00B7
      <a href="#" onclick="quickSearch('S&P 500');return false">S&P 500</a> \\u00B7
      <a href="#" onclick="quickSearch('election');return false">election</a>
    </div>
  </div>

  <div id="search-results" style="display:none"></div>
</div>

<script>
async function checkHealth() {
  const t0 = Date.now();
  try {
    await fetch('/health');
    const ms = Date.now() - t0;
    document.getElementById('dot').classList.add('on');
    document.getElementById('health-text').textContent = 'online \\u00B7 ' + ms + 'ms';
  } catch (e) {
    document.getElementById('health-text').textContent = 'offline';
  }
}

async function loadMarkets() {
  const container = document.getElementById('markets-container');
  try {
    const res = await fetch('/markets?status=open&limit=5');
    const data = await res.json();

    if (!data.markets || data.markets.length === 0) {
      container.innerHTML = '<div class="empty">No active markets found</div>';
      return;
    }

    container.innerHTML = data.markets.map(m => {
      const prob = m.yes_probability_pct || 50;
      const yesPrice = m.yes_price || prob;
      const noPrice = m.no_price || (100 - yesPrice);
      const title = (m.title || 'Untitled Market').substring(0, 80);
      const volume = m.volume ? `Vol: ${formatNumber(m.volume)}` : '';

      return `
        <div class="market-card">
          <div class="market-title">${escapeHtml(title)}</div>
          <div class="prob-bar-container">
            <div class="prob-bar-fill" style="width:${prob}%">
              <span class="prob-bar-pct">${prob}%</span>
            </div>
          </div>
          <div class="price-text">Yes \\u00A2${yesPrice.toFixed(0)} / No \\u00A2${noPrice.toFixed(0)}</div>
          ${volume ? `<div class="volume-text">${volume}</div>` : ''}
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="error">Failed to load markets: ${e.message}</div>`;
  }
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function handleSearch(event) {
  event.preventDefault();
  const input = document.getElementById('search-input');
  const query = input.value.trim();
  if (!query) return;

  await performSearch(query);
}

function quickSearch(query) {
  document.getElementById('search-input').value = query;
  performSearch(query);
}

async function performSearch(query) {
  const resultsDiv = document.getElementById('search-results');
  resultsDiv.style.display = 'block';
  resultsDiv.innerHTML = '<div class="card loading">Searching...</div>';

  try {
    const res = await fetch(`/search?query=${encodeURIComponent(query)}&limit=10`);
    const data = await res.json();

    if (!data.results || data.results.length === 0) {
      resultsDiv.innerHTML = `<div class="card empty">No results found for "${escapeHtml(query)}"</div>`;
      return;
    }

    const html = `
      <div class="card">
        <div class="section-title">Search Results for "${escapeHtml(query)}" (${data.count})</div>
        ${data.results.map(m => {
          const prob = m.yes_probability_pct || 50;
          const yesPrice = m.yes_price || prob;
          const noPrice = 100 - yesPrice;
          const title = (m.title || 'Untitled').substring(0, 80);
          const volume = m.volume ? `Vol: ${formatNumber(m.volume)}` : '';

          return `
            <div class="market-card">
              <div class="market-title">${escapeHtml(title)}</div>
              <div class="prob-bar-container">
                <div class="prob-bar-fill" style="width:${prob}%">
                  <span class="prob-bar-pct">${prob}%</span>
                </div>
              </div>
              <div class="price-text">Yes \\u00A2${yesPrice.toFixed(0)} / No \\u00A2${noPrice.toFixed(0)}</div>
              ${volume ? `<div class="volume-text">${volume}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
    resultsDiv.innerHTML = html;
  } catch (e) {
    resultsDiv.innerHTML = `<div class="card error">Search failed: ${e.message}</div>`;
  }
}

// Initialize
checkHealth();
loadMarkets();
</script>
</body>
</html>
"""


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _kalshi_request(path: str, params: dict | None = None) -> dict:
    """Make a request to Kalshi public API (no auth for market data)."""
    url = f"{BASE_URL}{path}"
    try:
        response = await http_client.get(url, params=params or {})
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Kalshi rate limit exceeded")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found on Kalshi")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unexpected error: {str(e)}")


# ── Endpoints ────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return HTMLResponse(content=HOME_HTML)


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": _ts()}


@app.get("/markets")
async def list_markets(
    status: str = Query("open", description="Market status: open, closed, settled"),
    series_ticker: str = Query(None, description="Filter by series ticker (e.g., KXHIGHNY)"),
    limit: int = Query(20, description="Max results", ge=1, le=100),
):
    """List prediction markets."""
    params = {"limit": limit, "status": status}
    if series_ticker:
        params["series_ticker"] = series_ticker

    data = await _kalshi_request("/markets", params)
    raw_markets = data.get("markets", [])

    markets = []
    for m in raw_markets:
        yes_price = m.get("yes_bid") or m.get("last_price")
        markets.append({
            "ticker": m.get("ticker"),
            "title": m.get("title") or m.get("subtitle"),
            "event_ticker": m.get("event_ticker"),
            "status": m.get("status"),
            "yes_price": yes_price,
            "no_price": (100 - yes_price) if yes_price is not None else None,
            "yes_probability_pct": yes_price,
            "volume": m.get("volume"),
            "open_interest": m.get("open_interest"),
            "close_time": m.get("close_time"),
            "expiration_time": m.get("expiration_time"),
        })

    return {"markets": markets, "count": len(markets), "timestamp": _ts()}


@app.get("/market")
async def get_market(ticker: str = Query(..., description="Market ticker (e.g., KXHIGHNY-25JUN30-T75)")):
    """Get a specific prediction market by ticker."""
    data = await _kalshi_request(f"/markets/{ticker}")
    m = data.get("market", data)

    yes_price = m.get("yes_bid") or m.get("last_price")

    return {
        "ticker": m.get("ticker"),
        "title": m.get("title") or m.get("subtitle"),
        "event_ticker": m.get("event_ticker"),
        "status": m.get("status"),
        "yes_price": yes_price,
        "no_price": (100 - yes_price) if yes_price is not None else None,
        "yes_probability_pct": yes_price,
        "volume": m.get("volume"),
        "open_interest": m.get("open_interest"),
        "close_time": m.get("close_time"),
        "expiration_time": m.get("expiration_time"),
        "result": m.get("result"),
        "rules_primary": m.get("rules_primary"),
        "floor_strike": m.get("floor_strike"),
        "cap_strike": m.get("cap_strike"),
        "timestamp": _ts(),
    }


@app.get("/events")
async def list_events(
    limit: int = Query(20, description="Max results", ge=1, le=100),
    status: str = Query(None, description="Filter by status: open, closed, settled"),
):
    """List prediction events (each event can have multiple markets)."""
    params = {"limit": limit}
    if status:
        params["status"] = status

    data = await _kalshi_request("/events", params)
    raw_events = data.get("events", [])

    events = []
    for e in raw_events:
        events.append({
            "event_ticker": e.get("event_ticker"),
            "title": e.get("title"),
            "category": e.get("category"),
            "sub_title": e.get("sub_title"),
            "mutually_exclusive": e.get("mutually_exclusive"),
            "market_count": len(e.get("markets", [])),
        })

    return {"events": events, "count": len(events), "timestamp": _ts()}


@app.get("/event")
async def get_event(ticker: str = Query(..., description="Event ticker (e.g., KXHIGHNY)")):
    """Get a specific event with its markets."""
    data = await _kalshi_request(f"/events/{ticker}")
    e = data.get("event", data)

    markets = []
    for m in (e.get("markets") or []):
        yes_price = m.get("yes_bid") or m.get("last_price")
        markets.append({
            "ticker": m.get("ticker"),
            "title": m.get("title") or m.get("subtitle"),
            "status": m.get("status"),
            "yes_price": yes_price,
            "yes_probability_pct": yes_price,
            "volume": m.get("volume"),
            "close_time": m.get("close_time"),
        })

    return {
        "event_ticker": e.get("event_ticker"),
        "title": e.get("title"),
        "category": e.get("category"),
        "sub_title": e.get("sub_title"),
        "markets": markets,
        "market_count": len(markets),
        "timestamp": _ts(),
    }


@app.get("/orderbook")
async def get_orderbook(ticker: str = Query(..., description="Market ticker")):
    """Get the orderbook for a market."""
    data = await _kalshi_request(f"/markets/{ticker}/orderbook")
    ob = data.get("orderbook", data)

    return {
        "ticker": ticker,
        "yes_bids": ob.get("yes", []),
        "no_bids": ob.get("no", []),
        "timestamp": _ts(),
    }


@app.get("/search")
async def search_markets(
    query: str = Query(..., description="Search query (e.g., 'fed rate', 'temperature', 'election')"),
    limit: int = Query(20, ge=1, le=50),
):
    """Search markets by keyword. Fetches open markets and filters by title."""
    # Kalshi doesn't have a search endpoint, so we fetch and filter
    data = await _kalshi_request("/markets", {"limit": 200, "status": "open"})
    raw_markets = data.get("markets", [])

    query_lower = query.lower()
    matched = []
    for m in raw_markets:
        title = (m.get("title") or m.get("subtitle") or "").lower()
        event = (m.get("event_ticker") or "").lower()
        if query_lower in title or query_lower in event:
            yes_price = m.get("yes_bid") or m.get("last_price")
            matched.append({
                "ticker": m.get("ticker"),
                "title": m.get("title") or m.get("subtitle"),
                "event_ticker": m.get("event_ticker"),
                "yes_price": yes_price,
                "yes_probability_pct": yes_price,
                "volume": m.get("volume"),
            })
            if len(matched) >= limit:
                break

    return {"query": query, "results": matched, "count": len(matched), "timestamp": _ts()}
