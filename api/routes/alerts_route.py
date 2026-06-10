"""
Price & Signal Alert Routes — CRUD for alert rules + proximity scanning.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import verify_token
from utils.alert_engine import (
    get_alerts, add_alert, delete_alert, reset_alert, CONDITION_LABELS,
)

router = APIRouter(tags=["alerts"])
logger = logging.getLogger(__name__)


class AddAlertRequest(BaseModel):
    ticker: str
    condition: str
    threshold: float


@router.get("/alerts")
async def list_alerts(_: str = Depends(verify_token)):
    alerts = get_alerts()
    return {"alerts": alerts, "condition_labels": CONDITION_LABELS}


@router.post("/alerts/add")
async def create_alert(body: AddAlertRequest, _: str = Depends(verify_token)):
    alert_id = add_alert(body.ticker, body.condition, body.threshold)
    return {"id": alert_id}


@router.delete("/alerts/{alert_id}")
async def remove_alert(alert_id: str, _: str = Depends(verify_token)):
    delete_alert(alert_id)
    return {"ok": True}


@router.post("/alerts/{alert_id}/reset")
async def reset(alert_id: str, _: str = Depends(verify_token)):
    reset_alert(alert_id)
    return {"ok": True}


class ProximityScanRequest(BaseModel):
    tickers: list[str]
    threshold_pts: float = 5.0  # points within BUY/SELL boundary to flag


@router.post("/alerts/proximity")
async def proximity_scan(body: ProximityScanRequest, _: str = Depends(verify_token)):
    """Scan watchlist tickers and flag those approaching a signal boundary."""
    from api.routes.stocks import _analyze_ticker
    from api.utils.verdict import _compute_verdict

    BUY_THRESHOLD = 60.0
    SELL_THRESHOLD = 45.0

    loop = asyncio.get_event_loop()
    approaching = []

    async def _check(ticker: str):
        try:
            analysis = await loop.run_in_executor(None, _analyze_ticker, ticker.upper(), "3mo")
            if analysis.error:
                return
            v = _compute_verdict(analysis)
            score = float(v.vf_score)
            gap_to_buy  = BUY_THRESHOLD  - score
            gap_to_sell = score - SELL_THRESHOLD

            if 0 < gap_to_buy <= body.threshold_pts:
                approaching.append({
                    "ticker": ticker, "score": score,
                    "signal": "APPROACHING_BUY",
                    "gap": round(gap_to_buy, 1),
                    "note": f"{round(gap_to_buy, 1)} pts from BUY signal",
                })
            elif 0 < gap_to_sell <= body.threshold_pts:
                approaching.append({
                    "ticker": ticker, "score": score,
                    "signal": "APPROACHING_SELL",
                    "gap": round(gap_to_sell, 1),
                    "note": f"{round(gap_to_sell, 1)} pts from SELL signal",
                })
        except Exception as exc:
            logger.warning("proximity_scan failed for %s: %s", ticker, exc)

    await asyncio.gather(*[_check(t) for t in body.tickers[:30]])
    return {"approaching": sorted(approaching, key=lambda x: x["gap"])}
