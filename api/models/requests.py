from __future__ import annotations
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class AnalyzeRequest(BaseModel):
    ticker: str
    period: str = "1y"


class BatchRequest(BaseModel):
    tickers: list[str]
    period: str = "1y"


class ScreenRequest(BaseModel):
    tickers: list[str]
    pe_min: float = 0
    pe_max: float = 200
    margin_min: float = 0
    roe_min: float = 0
    revenue_growth_min: float = -100


class PortfolioTextRequest(BaseModel):
    text: str


class RiskPosition(BaseModel):
    ticker: str
    shares: float
    entry_price: float


class RiskRequest(BaseModel):
    positions: list[RiskPosition]
