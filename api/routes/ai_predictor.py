from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import verify_token
from utils.stock_analyzer import StockAnalyzer
from utils.ai_predictor import AIPredictor

router = APIRouter(tags=["ai-predictor"])
logger = logging.getLogger(__name__)

_analyzer = StockAnalyzer()
_predictor = AIPredictor()


class SignalDetail(BaseModel):
    raw_score: float
    signal: str
    value: float
    weight: float


class PriceTargets(BaseModel):
    current: float
    conservative: float
    base: float
    aggressive: float


class AIPredictorResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    direction: str
    confidence: float
    bull_score: float
    weighted_sum: float
    signals: dict[str, SignalDetail]
    price_targets: PriceTargets
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    risk_reward: float
    time_horizon: str
    volatility_pct: float


@router.get("/ai-predictor/{ticker}", response_model=AIPredictorResponse)
async def get_ai_prediction(ticker: str, _: str = Depends(verify_token)):
    ticker = ticker.upper().strip()
    logger.info(f"AI prediction requested for {ticker}")

    data = _analyzer.get_stock_data(ticker, period="1y")
    if not data or data.get("history") is None or len(data.get("history", [])) < 50:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {ticker}")

    hist = _analyzer.calculate_technical_indicators(data["history"].copy())
    data["history"] = hist

    score    = _analyzer.calculate_score(data)
    metrics  = _analyzer.get_key_metrics(data)
    forecast = _analyzer.calculate_forecast(data, metrics, score)
    pred     = _predictor.predict(hist, metrics, score, forecast)

    return AIPredictorResponse(
        ticker=ticker,
        company_name=data.get("info", {}).get("longName", ticker),
        direction=pred["direction"],
        confidence=pred["confidence"],
        bull_score=pred["bull_score"],
        weighted_sum=pred["weighted_sum"],
        signals={k: SignalDetail(**v) for k, v in pred["signals"].items()},
        price_targets=PriceTargets(**pred["price_targets"]),
        entry=pred["entry"],
        stop_loss=pred["stop_loss"],
        tp1=pred["tp1"],
        tp2=pred["tp2"],
        tp3=pred["tp3"],
        risk_reward=pred["risk_reward"],
        time_horizon=pred["time_horizon"],
        volatility_pct=pred["volatility_pct"],
    )
