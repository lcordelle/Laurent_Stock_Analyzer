"""
Trade Journal Routes — CRUD for personal trade log + P&L summary.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from utils.trade_journal import (
    add_trade, close_trade, delete_trade,
    get_open_trades, get_closed_trades, get_pnl_summary, get_spy_return,
)

router = APIRouter(tags=["journal"])
logger = logging.getLogger(__name__)


class AddTradeRequest(BaseModel):
    ticker: str
    direction: str = "LONG"
    entry_date: str
    entry_price: float
    shares: float
    notes: str = ""
    tags: str = ""


class CloseTradeRequest(BaseModel):
    exit_date: str
    exit_price: float


@router.get("/journal/open")
async def list_open(_: str = Depends(verify_token)):
    return get_open_trades()


@router.get("/journal/closed")
async def list_closed(_: str = Depends(verify_token)):
    trades = get_closed_trades()
    for t in trades:
        if t.get("exit_date") and t.get("entry_date"):
            t["spy_return"] = get_spy_return(t["entry_date"], t["exit_date"])
            t["alpha"] = round(t.get("pnl_pct", 0) - t["spy_return"], 2)
    return trades


@router.get("/journal/summary")
async def pnl_summary(_: str = Depends(verify_token)):
    return get_pnl_summary()


@router.post("/journal/add")
async def add(_: str = Depends(verify_token), body: AddTradeRequest = ...):
    trade_id = add_trade(
        ticker=body.ticker,
        direction=body.direction,
        entry_date=body.entry_date,
        entry_price=body.entry_price,
        shares=body.shares,
        notes=body.notes,
        tags=body.tags,
    )
    return {"id": trade_id}


@router.post("/journal/{trade_id}/close")
async def close(trade_id: int, body: CloseTradeRequest,
                _: str = Depends(verify_token)):
    close_trade(trade_id, body.exit_date, body.exit_price)
    return {"ok": True}


@router.delete("/journal/{trade_id}")
async def delete(trade_id: int, _: str = Depends(verify_token)):
    delete_trade(trade_id)
    return {"ok": True}
