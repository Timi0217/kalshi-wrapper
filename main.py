import os
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
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
    return {
        "name": "Kalshi Wrapper",
        "description": "Prediction market data from Kalshi — event probabilities, market prices, and orderbooks for economics, politics, climate, tech, and more",
        "endpoints": [
            {"path": "/markets?status=open&limit=20", "description": "List prediction markets"},
            {"path": "/market?ticker=KXHIGHNY-25JUN30-T75", "description": "Get market by ticker"},
            {"path": "/events?limit=20", "description": "List events"},
            {"path": "/event?ticker=KXHIGHNY", "description": "Get event by ticker"},
            {"path": "/orderbook?ticker=KXHIGHNY-25JUN30-T75", "description": "Get market orderbook"},
            {"path": "/search?query=fed rate", "description": "Search markets"},
            {"path": "/health", "description": "Health check"},
        ],
    }


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
