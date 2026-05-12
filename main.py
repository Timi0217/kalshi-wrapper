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
  color:#fff;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  padding:40px 20px;
  line-height:1.6;
  animation:fadeIn 0.6s ease-out;
}
@keyframes fadeIn{
  from{opacity:0}
  to{opacity:1}
}
.container{
  max-width:600px;
  margin:0 auto;
}
.header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:12px;
}
.brand-group{
  display:flex;
  align-items:center;
  gap:14px;
}
.brand-icon{
  width:48px;
  height:48px;
  border-radius:14px;
  background:linear-gradient(135deg, #00D632, #00A828);
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:24px;
  font-weight:800;
  color:#0a0a0a;
}
.brand-text h1{
  font-size:24px;
  font-weight:700;
  color:#fff;
  margin-bottom:2px;
}
.brand-text .subtitle{
  font-size:13px;
  color:#555;
  line-height:1.3;
}
.health-badge{
  display:flex;
  align-items:center;
  gap:6px;
  font-size:12px;
  color:#555;
}
.health-dot{
  width:6px;
  height:6px;
  border-radius:50%;
  background:#333;
  transition:background 0.3s;
}
.health-dot.on{
  background:#00D632;
  box-shadow:0 0 8px rgba(0,214,50,0.5);
}
.section-label{
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:2px;
  color:#555;
  font-weight:600;
  margin:32px 0 16px 0;
  display:flex;
  align-items:center;
  gap:10px;
}
.live-badge{
  background:linear-gradient(135deg, #00D632, #00A828);
  color:#0a0a0a;
  font-size:9px;
  padding:3px 8px;
  border-radius:4px;
  font-weight:700;
  letter-spacing:1px;
}
.category-chips{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  margin:24px 0;
}
.chip{
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:20px;
  padding:5px 14px;
  font-size:12px;
  color:#555;
  cursor:pointer;
  transition:all 0.2s;
}
.chip:hover{
  border-color:rgba(0,214,50,0.4);
  color:#00D632;
}
.markets-grid{
  display:grid;
  gap:12px;
  margin-bottom:32px;
}
.market-card{
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;
  padding:18px;
  transition:all 0.3s ease;
  animation:fadeInUp 0.5s ease-out;
  animation-fill-mode:both;
}
.market-card:nth-child(1){animation-delay:0.05s}
.market-card:nth-child(2){animation-delay:0.1s}
.market-card:nth-child(3){animation-delay:0.15s}
.market-card:nth-child(4){animation-delay:0.2s}
.market-card:nth-child(5){animation-delay:0.25s}
.market-card:nth-child(6){animation-delay:0.3s}
@keyframes fadeInUp{
  from{
    opacity:0;
    transform:translateY(20px);
  }
  to{
    opacity:1;
    transform:translateY(0);
  }
}
.market-card:hover{
  background:rgba(255,255,255,0.05);
  border-color:rgba(255,255,255,0.12);
  transform:translateY(-2px);
}
.category-tag{
  display:inline-block;
  font-size:10px;
  font-weight:600;
  padding:4px 8px;
  border-radius:6px;
  text-transform:uppercase;
  letter-spacing:0.5px;
  margin-bottom:10px;
}
.cat-economics{background:rgba(52,152,219,0.15);color:#3498db}
.cat-politics{background:rgba(155,89,182,0.15);color:#9b59b6}
.cat-climate{background:rgba(46,204,113,0.15);color:#2ecc71}
.cat-tech{background:rgba(52,211,153,0.15);color:#34d399}
.cat-sports{background:rgba(241,196,15,0.15);color:#f1c40f}
.cat-crypto{background:rgba(230,126,34,0.15);color:#e67e22}
.cat-entertainment{background:rgba(231,76,60,0.15);color:#e74c3c}
.cat-commodities{background:rgba(149,117,205,0.15);color:#9575cd}
.cat-default{background:rgba(139,148,158,0.15);color:#8B949E}
.market-title{
  font-size:14px;
  font-weight:600;
  color:#fff;
  margin-bottom:12px;
  line-height:1.4;
}
.prob-bar-container{
  background:rgba(255,255,255,0.04);
  height:26px;
  border-radius:6px;
  overflow:hidden;
  position:relative;
  margin-bottom:10px;
}
.prob-bar-fill{
  background:linear-gradient(90deg, #00D632, #00A828);
  height:100%;
  transition:width 0.6s cubic-bezier(0.4,0,0.2,1);
  display:flex;
  align-items:center;
  justify-content:flex-end;
  padding:0 10px;
}
.prob-pct{
  color:#0a0a0a;
  font-size:12px;
  font-weight:700;
  font-family:'SF Mono',Monaco,Consolas,monospace;
  z-index:1;
}
.volume-text{
  font-size:12px;
  color:#444;
  font-family:'SF Mono',Monaco,Consolas,monospace;
}
.search-card{
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;
  padding:24px;
  margin-top:32px;
}
.search-form{
  display:flex;
  gap:10px;
  margin-bottom:16px;
}
.search-input{
  flex:1;
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:10px;
  padding:12px 16px;
  color:#fff;
  font-size:14px;
  outline:none;
  transition:all 0.2s;
}
.search-input:focus{
  border-color:rgba(0,214,50,0.4);
  background:rgba(255,255,255,0.06);
}
.search-input::placeholder{
  color:#555;
}
.search-btn{
  background:linear-gradient(135deg, #00D632, #00A828);
  color:#0a0a0a;
  border:none;
  border-radius:10px;
  padding:12px 24px;
  font-size:14px;
  font-weight:700;
  cursor:pointer;
  transition:all 0.2s;
}
.search-btn:hover{
  transform:translateY(-1px);
  box-shadow:0 4px 16px rgba(0,214,50,0.3);
}
.search-btn:active{
  transform:translateY(0);
}
.quick-pills{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
}
.quick-pill{
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.06);
  border-radius:16px;
  padding:4px 12px;
  font-size:11px;
  color:#555;
  text-decoration:none;
  transition:all 0.2s;
}
.quick-pill:hover{
  border-color:rgba(0,214,50,0.4);
  color:#00D632;
}
.loading{
  text-align:center;
  color:#555;
  padding:32px;
  font-size:14px;
}
.loading::after{
  content:'...';
  animation:dots 1.5s steps(4,end) infinite;
}
@keyframes dots{
  0%,20%{content:''}
  40%{content:'.'}
  60%{content:'..'}
  80%,100%{content:'...'}
}
.error{
  color:#f85149;
  background:rgba(248,81,73,0.1);
  padding:16px;
  border-radius:10px;
  font-size:13px;
  border:1px solid rgba(248,81,73,0.3);
}
.empty{
  text-align:center;
  color:#555;
  padding:32px;
  font-size:14px;
}
#search-results{
  margin-top:20px;
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="brand-group">
      <div class="brand-icon">K</div>
      <div class="brand-text">
        <h1>Kalshi</h1>
        <div class="subtitle">Regulated prediction markets — economics, politics, climate, tech</div>
      </div>
    </div>
    <div class="health-badge">
      <span class="health-dot" id="dot"></span>
      <span id="health-text">connecting...</span>
    </div>
  </div>

  <div class="category-chips">
    <span class="chip">Trending</span>
    <span class="chip">Economics</span>
    <span class="chip">Politics</span>
    <span class="chip">Climate</span>
    <span class="chip">Tech</span>
    <span class="chip">Entertainment</span>
    <span class="chip">Sports</span>
  </div>

  <div class="section-label">
    TRENDING MARKETS
    <span class="live-badge">LIVE</span>
  </div>

  <div class="markets-grid" id="trending-container">
    <div class="loading">Loading trending markets</div>
  </div>

  <div class="search-card">
    <form class="search-form" onsubmit="handleSearch(event)">
      <input type="text" class="search-input" id="search-input" placeholder="Search markets... (e.g., 'Fed rate', 'inflation')" autocomplete="off">
      <button type="submit" class="search-btn">Search</button>
    </form>
    <div class="quick-pills">
      <a href="#" class="quick-pill" onclick="quickSearch('GDP');return false">GDP</a>
      <a href="#" class="quick-pill" onclick="quickSearch('inflation');return false">inflation</a>
      <a href="#" class="quick-pill" onclick="quickSearch('S&P 500');return false">S&P 500</a>
      <a href="#" class="quick-pill" onclick="quickSearch('election');return false">election</a>
    </div>
  </div>

  <div id="search-results"></div>
</div>

<script>
async function checkHealth() {
  const t0 = Date.now();
  try {
    await fetch('/health');
    const ms = Date.now() - t0;
    document.getElementById('dot').classList.add('on');
    document.getElementById('health-text').textContent = 'online · ' + ms + 'ms';
  } catch (e) {
    document.getElementById('health-text').textContent = 'offline';
  }
}

async function loadTrending() {
  const container = document.getElementById('trending-container');
  try {
    const res = await fetch('/trending?limit=6');
    const data = await res.json();

    if (!data.markets || data.markets.length === 0) {
      container.innerHTML = '<div class="empty">No trending markets available</div>';
      return;
    }

    container.innerHTML = data.markets.map(m => {
      const prob = m.yes_probability_pct || 50;
      const category = (m.category || 'default').toLowerCase().replace(/[^a-z]/g, '');
      const title = (m.title || 'Untitled Market');
      const volume = m.volume ? formatNumber(m.volume) : '—';
      const catClass = 'cat-' + category;
      const catDisplay = (m.category || 'Market').toUpperCase();

      return `
        <div class="market-card">
          <div class="category-tag ${catClass}">${escapeHtml(catDisplay)}</div>
          <div class="market-title">${escapeHtml(title)}</div>
          <div class="prob-bar-container">
            <div class="prob-bar-fill" style="width:${prob}%">
              <span class="prob-pct">${prob}%</span>
            </div>
          </div>
          <div class="volume-text">Vol $${volume}</div>
        </div>
      `;
    }).join('');
  } catch (e) {
    container.innerHTML = `<div class="error">Failed to load trending markets: ${e.message}</div>`;
  }
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toFixed(0);
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
  resultsDiv.innerHTML = '<div class="loading">Searching</div>';

  try {
    const res = await fetch(`/search?query=${encodeURIComponent(query)}&limit=10`);
    const data = await res.json();

    if (!data.results || data.results.length === 0) {
      resultsDiv.innerHTML = `<div class="empty">No results found for "${escapeHtml(query)}"</div>`;
      return;
    }

    const html = `
      <div class="section-label" style="margin-top:40px">
        SEARCH RESULTS
      </div>
      <div class="markets-grid">
        ${data.results.map(m => {
          const prob = m.yes_probability_pct || 50;
          const category = (m.category || 'default').toLowerCase().replace(/[^a-z]/g, '');
          const title = (m.title || 'Untitled');
          const volume = m.volume ? formatNumber(m.volume) : '—';
          const catClass = 'cat-' + category;
          const catDisplay = (m.category || 'Market').toUpperCase();

          return `
            <div class="market-card">
              <div class="category-tag ${catClass}">${escapeHtml(catDisplay)}</div>
              <div class="market-title">${escapeHtml(title)}</div>
              <div class="prob-bar-container">
                <div class="prob-bar-fill" style="width:${prob}%">
                  <span class="prob-pct">${prob}%</span>
                </div>
              </div>
              <div class="volume-text">Vol $${volume}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
    resultsDiv.innerHTML = html;
  } catch (e) {
    resultsDiv.innerHTML = `<div class="error">Search failed: ${e.message}</div>`;
  }
}

// Initialize
checkHealth();
loadTrending();
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
    """List prediction markets. Excludes MVE (multi-game parlays)."""
    params = {"limit": limit, "status": status, "mve_filter": "exclude"}
    if series_ticker:
        params["series_ticker"] = series_ticker

    data = await _kalshi_request("/markets", params)
    raw_markets = data.get("markets", [])

    markets = []
    for m in raw_markets:
        # Use yes_bid_dollars from raw API, fallback to last_price
        yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
        yes_price = None
        if yes_bid_str:
            try:
                yes_price = float(yes_bid_str) * 100  # Convert to percentage
            except (ValueError, TypeError):
                yes_price = None

        # Use volume_fp from raw API
        volume_str = m.get("volume_fp") or m.get("volume")
        volume = None
        if volume_str:
            try:
                volume = float(volume_str)
            except (ValueError, TypeError):
                volume = 0

        markets.append({
            "ticker": m.get("ticker"),
            "title": m.get("title") or m.get("subtitle"),
            "event_ticker": m.get("event_ticker"),
            "status": m.get("status"),
            "yes_price": yes_price,
            "no_price": (100 - yes_price) if yes_price is not None else None,
            "yes_probability_pct": yes_price,
            "volume": volume,
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

    # Use yes_bid_dollars from raw API
    yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
    yes_price = None
    if yes_bid_str:
        try:
            yes_price = float(yes_bid_str) * 100  # Convert to percentage
        except (ValueError, TypeError):
            yes_price = None

    # Use volume_fp from raw API
    volume_str = m.get("volume_fp") or m.get("volume")
    volume = None
    if volume_str:
        try:
            volume = float(volume_str)
        except (ValueError, TypeError):
            volume = 0

    return {
        "ticker": m.get("ticker"),
        "title": m.get("title") or m.get("subtitle"),
        "event_ticker": m.get("event_ticker"),
        "status": m.get("status"),
        "yes_price": yes_price,
        "no_price": (100 - yes_price) if yes_price is not None else None,
        "yes_probability_pct": yes_price,
        "volume": volume,
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
    """List prediction events with nested markets (each event can have multiple markets)."""
    params = {"limit": limit, "with_nested_markets": "true"}
    if status:
        params["status"] = status

    data = await _kalshi_request("/events", params)
    raw_events = data.get("events", [])

    events = []
    for e in raw_events:
        markets = []
        for m in (e.get("markets") or []):
            # Extract real data from nested markets
            yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
            yes_price = None
            if yes_bid_str:
                try:
                    yes_price = float(yes_bid_str) * 100  # Convert to percentage
                except (ValueError, TypeError):
                    yes_price = None

            volume_str = m.get("volume_fp") or m.get("volume")
            volume = 0
            if volume_str:
                try:
                    volume = float(volume_str)
                except (ValueError, TypeError):
                    volume = 0

            markets.append({
                "ticker": m.get("ticker"),
                "title": m.get("title") or m.get("subtitle"),
                "status": m.get("status"),
                "yes_price": yes_price,
                "yes_probability_pct": yes_price,
                "volume": volume,
                "close_time": m.get("close_time"),
            })

        events.append({
            "event_ticker": e.get("event_ticker"),
            "title": e.get("title"),
            "category": e.get("category"),
            "sub_title": e.get("sub_title"),
            "mutually_exclusive": e.get("mutually_exclusive"),
            "market_count": len(markets),
            "markets": markets,
        })

    return {"events": events, "count": len(events), "timestamp": _ts()}


@app.get("/event")
async def get_event(ticker: str = Query(..., description="Event ticker (e.g., KXHIGHNY)")):
    """Get a specific event with its markets."""
    data = await _kalshi_request(f"/events/{ticker}")
    e = data.get("event", data)

    markets = []
    for m in (e.get("markets") or []):
        yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
        yes_price = None
        if yes_bid_str:
            try:
                yes_price = float(yes_bid_str) * 100  # Convert to percentage
            except (ValueError, TypeError):
                yes_price = None

        volume_str = m.get("volume_fp") or m.get("volume")
        volume = 0
        if volume_str:
            try:
                volume = float(volume_str)
            except (ValueError, TypeError):
                volume = 0

        markets.append({
            "ticker": m.get("ticker"),
            "title": m.get("title") or m.get("subtitle"),
            "status": m.get("status"),
            "yes_price": yes_price,
            "yes_probability_pct": yes_price,
            "volume": volume,
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


@app.get("/trending")
async def get_trending(
    limit: int = Query(10, description="Max results", ge=1, le=50),
):
    """Get trending markets sorted by volume. Excludes multi-game parlays."""
    # Fetch events with nested markets
    data = await _kalshi_request("/events", {"limit": 50, "status": "open", "with_nested_markets": "true"})
    raw_events = data.get("events", [])

    # Collect all markets from all events
    all_markets = []
    for e in raw_events:
        event_title = e.get("title", "")
        event_category = e.get("category", "")
        for m in (e.get("markets") or []):
            market_title = m.get("title") or m.get("subtitle") or ""

            # Filter out parlay markets (they have lots of commas in the title)
            comma_count = market_title.count(",")
            if comma_count > 3:  # Skip if more than 3 commas (likely a parlay)
                continue

            # Use yes_bid_dollars from raw API
            yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
            yes_price = None
            if yes_bid_str:
                try:
                    yes_price = float(yes_bid_str) * 100  # Convert to percentage
                except (ValueError, TypeError):
                    yes_price = None

            # Use volume_fp from raw API and convert to float
            volume_str = m.get("volume_fp") or m.get("volume")
            volume = 0
            if volume_str:
                try:
                    volume = float(volume_str)
                except (ValueError, TypeError):
                    volume = 0

            all_markets.append({
                "ticker": m.get("ticker"),
                "title": market_title,
                "event_title": event_title,
                "category": event_category,
                "yes_price": yes_price,
                "yes_probability_pct": yes_price,
                "volume": volume,
                "status": m.get("status"),
            })

    # Sort by volume descending
    all_markets.sort(key=lambda x: x.get("volume") or 0, reverse=True)

    # Return top N
    top_markets = all_markets[:limit]

    return {"markets": top_markets, "count": len(top_markets), "timestamp": _ts()}


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
    """Search markets by keyword. Uses events endpoint to get quality data."""
    # Fetch events with nested markets instead of raw markets endpoint
    data = await _kalshi_request("/events", {"limit": 100, "status": "open", "with_nested_markets": "true"})
    raw_events = data.get("events", [])

    query_lower = query.lower()
    matched = []

    # Collect all markets from all events
    for e in raw_events:
        event_title = (e.get("title") or "").lower()
        event_category = (e.get("category") or "").lower()
        event_ticker = (e.get("event_ticker") or "").lower()

        for m in (e.get("markets") or []):
            market_title = (m.get("title") or m.get("subtitle") or "")
            market_title_lower = market_title.lower()

            # Filter out parlays
            comma_count = market_title.count(",")
            if comma_count > 3:
                continue

            # Match against market title, event title, or category
            if (query_lower in market_title_lower or
                query_lower in event_title or
                query_lower in event_category or
                query_lower in event_ticker):

                # Use yes_bid_dollars from raw API
                yes_bid_str = m.get("yes_bid_dollars") or m.get("yes_bid")
                yes_price = None
                if yes_bid_str:
                    try:
                        yes_price = float(yes_bid_str) * 100  # Convert to percentage
                    except (ValueError, TypeError):
                        yes_price = None

                # Use volume_fp from raw API and convert to float
                volume_str = m.get("volume_fp") or m.get("volume")
                volume = 0
                if volume_str:
                    try:
                        volume = float(volume_str)
                    except (ValueError, TypeError):
                        volume = 0

                matched.append({
                    "ticker": m.get("ticker"),
                    "title": market_title,
                    "event_ticker": e.get("event_ticker"),
                    "category": e.get("category"),
                    "yes_price": yes_price,
                    "yes_probability_pct": yes_price,
                    "volume": volume,
                })

    # Sort by volume descending
    matched.sort(key=lambda x: x.get("volume") or 0, reverse=True)

    # Limit results
    matched = matched[:limit]

    return {"query": query, "results": matched, "count": len(matched), "timestamp": _ts()}
