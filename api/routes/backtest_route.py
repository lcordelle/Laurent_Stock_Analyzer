"""
Backtesting Route — run strategy simulations on historical data.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import verify_token
from utils.backtesting import run_backtest, STRATEGIES

router = APIRouter(tags=["backtest"])
logger = logging.getLogger(__name__)


class BacktestRequest(BaseModel):
    ticker: str
    strategy: str = "ma_crossover"
    period: str = "2y"
    initial_capital: float = 10000.0


@router.get("/backtest/strategies")
async def list_strategies(_: str = Depends(verify_token)):
    return {"strategies": STRATEGIES}


@router.post("/backtest/run")
async def run(body: BacktestRequest, _: str = Depends(verify_token)):
    from fastapi import HTTPException
    if body.strategy not in STRATEGIES:
        raise HTTPException(422, detail=f"Unknown strategy '{body.strategy}'. Valid: {list(STRATEGIES)}")
    result = run_backtest(
        ticker=body.ticker,
        strategy=body.strategy,
        period=body.period,
        initial_capital=body.initial_capital,
    )
    return result
