from __future__ import annotations
import asyncio
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token
from api.routes.opportunities import _quick_scan

router = APIRouter(tags=["watchlist"])
logger = logging.getLogger(__name__)


class WatchlistRequest(BaseModel):
    tickers: list[str]


@router.post("/watchlist/signals")
async def watchlist_signals(body: WatchlistRequest, _: str = Depends(verify_token)):
    tickers = body.tickers[:60]
    loop = asyncio.get_event_loop()

    async def fetch(t: str):
        return await loop.run_in_executor(None, _quick_scan, t)

    results = await asyncio.gather(*[fetch(t) for t in tickers], return_exceptions=True)

    signals = []
    failed = []
    for i, r in enumerate(results):
        if isinstance(r, dict) and r is not None:
            signals.append(r)
        else:
            failed.append(tickers[i])

    return {"signals": signals, "failed": failed}
