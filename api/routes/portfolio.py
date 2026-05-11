import asyncio
import logging
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, Depends
from api.auth import verify_token
from api.models.requests import PortfolioTextRequest, RiskRequest
from utils.portfolio_analyzer import PortfolioAnalyzer
from utils.portfolio_risk import PortfolioRiskManager
from utils.stock_analyzer import StockAnalyzer
from api.routes.stocks import _compute_trading_signals

router = APIRouter(tags=["portfolio"])
logger = logging.getLogger(__name__)

_stock_analyzer = StockAnalyzer()


def _df_to_dict(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: _df_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_df_to_dict(i) for i in obj]
    return obj


def _holding_signals(ticker: str, current_price: float, info: dict) -> dict:
    try:
        hist = yf.Ticker(ticker).history(period="6mo")
        if hist is None or len(hist) < 20:
            return {}
        if len(hist) >= 50:
            hist = _stock_analyzer.calculate_technical_indicators(hist.copy())
        sig = _compute_trading_signals(hist, current_price)
        score = _stock_analyzer.calculate_score({"info": info, "history": hist})
        vf_score = score.get("total_score", 0) if isinstance(score, dict) else 0
        return {
            "signal": sig.signal,
            "confidence": sig.confidence,
            "rsi": sig.rsi_value,
            "rsi_signal": sig.rsi_signal,
            "macd_signal": sig.macd_signal,
            "trend": sig.trend_strength,
            "stop_loss": sig.stop_loss,
            "tp1": sig.tp1,
            "tp2": sig.tp2,
            "tp3": sig.tp3,
            "risk_reward": sig.risk_reward,
            "vf_score": vf_score,
        }
    except Exception as e:
        logger.warning(f"Signal computation failed for {ticker}: {e}")
        return {}


def _run_portfolio_analysis(text: str) -> dict:
    analyzer = PortfolioAnalyzer()
    holdings = analyzer.parse_portfolio_input(text)
    if not holdings:
        return {"error": "Could not parse portfolio data", "holdings": {}}
    portfolio_data = analyzer.get_portfolio_data(holdings)
    if not portfolio_data:
        return {"error": "Could not fetch market data for portfolio tickers", "holdings": {}}
    result = analyzer.calculate_portfolio_metrics(portfolio_data)
    if not result:
        return {}
    for ticker, data in portfolio_data.items():
        sigs = _holding_signals(ticker, data["current_price"], data.get("info", {}))
        data["signals"] = sigs
    result["portfolio_data"] = portfolio_data
    return _df_to_dict(result)


def _run_risk_analysis(positions: list[dict]) -> dict:
    manager = PortfolioRiskManager()
    for pos in positions:
        try:
            ticker_obj = yf.Ticker(pos["ticker"])
            hist = ticker_obj.history(period="1d")
            pos["current_price"] = float(hist["Close"].iloc[-1]) if len(hist) > 0 else pos["entry_price"]
        except Exception:
            pos["current_price"] = pos["entry_price"]

    result = manager.calculate_portfolio_metrics(positions)
    return _df_to_dict(result) if result else {}


@router.post("/portfolio/analyze")
async def portfolio_analyze(body: PortfolioTextRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_portfolio_analysis, body.text)


@router.post("/portfolio/risk")
async def portfolio_risk(body: RiskRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    positions = [p.model_dump() for p in body.positions]
    return await loop.run_in_executor(None, _run_risk_analysis, positions)
