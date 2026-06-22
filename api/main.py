import sys
import os
import json
import math
import asyncio
import logging
import time
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # triggers logging setup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from api.routes import auth, stocks, screener, portfolio, reports, opportunities, market_pulse, ai_research, watchlist, penny_stocks, grades, alerts_route, news


def _scrub(obj):
    """Recursively replace NaN/Inf floats with None so JSON serialization never fails."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_scrub(v) for v in obj]
    return obj


class _SafeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            _scrub(content),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

logger = logging.getLogger(__name__)


async def _scan_loop():
    # Wait 60s on startup so uvicorn --reload doesn't slam yfinance on every file save.
    # If the cache is fresh (< half TTL), skip the first scan entirely.
    await asyncio.sleep(60)
    age = time.time() - opportunities._cache_ts
    if age < opportunities.CACHE_TTL / 2:
        logger.info("Opportunities cache is fresh (%.0fs old), skipping startup scan", age)
    else:
        try:
            await opportunities._run_scan()
            await opportunities._two_pass_scan()
        except Exception as e:
            logger.error("Background scan failed: %s", e)
    while True:
        await asyncio.sleep(opportunities.CACHE_TTL)
        try:
            await opportunities._run_scan()
            await opportunities._two_pass_scan()
        except Exception as e:
            logger.error("Background scan failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_scan_loop())
    from utils.alert_engine import start_alert_engine
    start_alert_engine()
    yield


app = FastAPI(title="VirtualFusion Stock Analyzer API", version="2.0", lifespan=lifespan,
             default_response_class=_SafeJSONResponse)

_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3002",
]
_public_url = os.getenv("PUBLIC_URL", "").strip().rstrip("/")
if _public_url:
    _CORS_ORIGINS.append(_public_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(screener.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(opportunities.router, prefix="/api")
app.include_router(market_pulse.router, prefix="/api")
app.include_router(ai_research.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(penny_stocks.router, prefix="/api")
app.include_router(grades.router, prefix="/api")
app.include_router(alerts_route.router, prefix="/api")
app.include_router(news.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0"}


@app.get("/api/bundle-version")
async def bundle_version():
    """Returns the current JS bundle hash so the frontend can detect stale loads."""
    import glob
    js_files = glob.glob(os.path.join(_DIST, "assets", "index-*.js"))
    bundle = os.path.basename(js_files[0]) if js_files else "unknown"
    return {"bundle": bundle}


# Serve built React frontend — must be last so /api routes take priority
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        candidate = os.path.join(_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        with open(os.path.join(_DIST, "index.html"), "rb") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
        )
