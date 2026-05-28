"""
Price & Signal Alert Routes — CRUD for alert rules.
"""
from __future__ import annotations

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
