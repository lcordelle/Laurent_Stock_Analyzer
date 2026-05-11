import asyncio
import logging
from fastapi import APIRouter, Depends
from api.auth import verify_token
from api.models.requests import ScreenRequest
from api.models.responses import ScreenerResult
from api.routes.stocks import _analyze_ticker

router = APIRouter(tags=["screener"])
logger = logging.getLogger(__name__)


def _passes_filters(analysis, req: ScreenRequest) -> bool:
    m = analysis.metrics
    if m is None:
        return False

    pe = m.pe_ratio
    if pe is not None:
        if pe < req.pe_min or pe > req.pe_max:
            return False

    gross_margin = m.gross_margin
    if gross_margin is None or gross_margin < req.margin_min:
        return False

    roe = m.roe
    if roe is None or roe < req.roe_min:
        return False

    rev_growth = m.revenue_growth
    if rev_growth is None or rev_growth < req.revenue_growth_min:
        return False

    return True


@router.post("/screen", response_model=ScreenerResult)
async def screen(body: ScreenRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()

    async def _fetch_one(ticker: str):
        return await loop.run_in_executor(None, _analyze_ticker, ticker, "1y")

    tasks = [_fetch_one(t) for t in body.tickers]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    passing = []
    for ticker, outcome in zip(body.tickers, outcomes):
        if isinstance(outcome, Exception):
            logger.error("Screener fetch failed for %s: %s", ticker, outcome)
            continue
        if outcome.error:
            continue
        if _passes_filters(outcome, body):
            passing.append(outcome)

    return ScreenerResult(
        results=passing,
        total_screened=len(body.tickers),
        total_passed=len(passing),
    )
