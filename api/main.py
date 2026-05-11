import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # triggers logging setup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, stocks, screener, portfolio, reports, opportunities, market_pulse, ai_research, watchlist, penny_stocks, ai_predictor, grades

app = FastAPI(title="VirtualFusion Stock Analyzer API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3002",
        "https://laurent.ngrok.io",
    ],
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
app.include_router(ai_predictor.router, prefix="/api")
app.include_router(grades.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0"}
