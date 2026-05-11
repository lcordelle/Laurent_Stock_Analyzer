import asyncio
import tempfile
import os
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from api.auth import verify_token
from api.routes.stocks import _analyze_ticker
from utils.stock_analyzer import StockAnalyzer
from report_generator import StockReportGenerator

router = APIRouter(tags=["reports"])
logger = logging.getLogger(__name__)


def _generate_report(ticker: str, period: str) -> str:
    analyzer = StockAnalyzer()
    data = analyzer.get_stock_data(ticker, period)
    if not data or "error" in data:
        raise ValueError(f"Could not fetch data for {ticker}: {data.get('error') if data else 'unknown'}")

    metrics = analyzer.get_key_metrics(data)
    score = analyzer.calculate_score(data)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    generator = StockReportGenerator()
    generator.generate_single_stock_report(ticker, data, metrics, score, tmp.name)
    return tmp.name


@router.get("/report/{ticker}")
async def get_report(
    ticker: str,
    background_tasks: BackgroundTasks,
    period: str = Query("1y"),
    _: str = Depends(verify_token),
):
    loop = asyncio.get_event_loop()
    pdf_path = await loop.run_in_executor(None, _generate_report, ticker.upper(), period)
    background_tasks.add_task(os.unlink, pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{ticker.upper()}_analysis.pdf",
    )
