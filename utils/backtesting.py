"""
Simple Backtesting Engine
Supports MA crossover and RSI strategies on historical yfinance data.
Compares performance vs SPY benchmark.
"""

import logging
from datetime import datetime

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

STRATEGIES = {
    'ma_crossover': 'MA Crossover (SMA20 > SMA50)',
    'rsi': 'RSI Strategy (Buy <30, Sell >70)',
    'golden_cross': 'Golden Cross (SMA50 > SMA200)',
}


def _fetch(ticker: str, period: str) -> pd.DataFrame:
    hist = yf.Ticker(ticker).history(period=period)
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    return hist[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()


def _generate_signals(hist: pd.DataFrame, strategy: str) -> pd.Series:
    """Return a Series of 1 (long) or 0 (flat) positions."""
    signals = pd.Series(0, index=hist.index)

    if strategy == 'ma_crossover':
        sma20 = hist['Close'].rolling(20).mean()
        sma50 = hist['Close'].rolling(50).mean()
        signals = (sma20 > sma50).astype(int)

    elif strategy == 'golden_cross':
        sma50 = hist['Close'].rolling(50).mean()
        sma200 = hist['Close'].rolling(200).mean()
        signals = (sma50 > sma200).astype(int)

    elif strategy == 'rsi':
        delta = hist['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float('nan'))
        rsi = 100 - (100 / (1 + rs))
        in_position = False
        pos = pd.Series(0, index=hist.index)
        for i in range(len(rsi)):
            if pd.isna(rsi.iloc[i]):
                continue
            if not in_position and rsi.iloc[i] < 30:
                in_position = True
            elif in_position and rsi.iloc[i] > 70:
                in_position = False
            pos.iloc[i] = 1 if in_position else 0
        signals = pos

    return signals


def _sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
    std = returns.std()
    if len(returns) == 0 or std == 0 or (std != std):  # len 0 or zero/NaN std
        return 0.0
    return round(float(returns.mean() / std * (periods_per_year ** 0.5)), 2)


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return round(float(drawdown.min() * 100), 2)


def run_backtest(ticker: str, strategy: str = 'ma_crossover',
                 period: str = '2y', initial_capital: float = 10000.0) -> dict:
    """Run a backtest and return metrics + equity series for charting.

    Returns dict with keys:
      equity_curve, spy_curve, metrics, trades, error
    """
    result = {
        'equity_curve': [],
        'spy_curve': [],
        'metrics': {},
        'trades': [],
        'error': None,
        'strategy_label': STRATEGIES.get(strategy, strategy),
        'ticker': ticker.upper(),
        'period': period,
    }

    try:
        hist = _fetch(ticker, period)
        spy_hist = _fetch('SPY', period)

        if len(hist) < 60:
            result['error'] = f'Insufficient history ({len(hist)} days). Need at least 60.'
            return result

        signals = _generate_signals(hist, strategy)
        signals = signals.shift(1).fillna(0)  # avoid look-ahead: trade next day

        # Daily returns
        daily_ret = hist['Close'].pct_change().fillna(0)
        strategy_ret = daily_ret * signals

        # Equity curves
        equity = initial_capital * (1 + strategy_ret).cumprod()
        spy_ret = spy_hist['Close'].pct_change().fillna(0)

        # Align SPY to same dates
        common = equity.index.intersection(spy_hist.index)
        spy_equity = initial_capital * (1 + spy_ret.reindex(common).fillna(0)).cumprod()

        # Serialize for plotly
        result['equity_curve'] = [
            {'date': str(d.date()), 'value': round(v, 2)}
            for d, v in equity.items()
        ]
        result['spy_curve'] = [
            {'date': str(d.date()), 'value': round(v, 2)}
            for d, v in spy_equity.items()
        ]

        # Metrics
        final_val = float(equity.iloc[-1])
        total_return = (final_val - initial_capital) / initial_capital * 100
        spy_final = float(spy_equity.iloc[-1]) if len(spy_equity) else initial_capital
        spy_return = (spy_final - initial_capital) / initial_capital * 100

        sharpe = _sharpe(strategy_ret[strategy_ret != 0])
        max_dd = _max_drawdown(equity)

        # Win rate from individual trade segments
        position_changes = signals.diff().fillna(0)
        entries = hist.index[position_changes == 1].tolist()
        exits = hist.index[position_changes == -1].tolist()
        wins, total_trades = 0, 0
        for entry in entries:
            next_exits = [e for e in exits if e > entry]
            if next_exits:
                exit_date = next_exits[0]
                entry_price = hist.loc[entry, 'Close']
                exit_price = hist.loc[exit_date, 'Close']
                trade_ret = (exit_price - entry_price) / entry_price * 100
                if trade_ret > 0:
                    wins += 1
                total_trades += 1

        win_rate = round(wins / total_trades * 100, 1) if total_trades else 0

        result['metrics'] = {
            'total_return': round(total_return, 2),
            'spy_return': round(spy_return, 2),
            'alpha': round(total_return - spy_return, 2),
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_value': round(final_val, 2),
            'initial_capital': initial_capital,
        }

    except Exception as e:
        result['error'] = str(e)
        logger.error("Backtest error %s %s: %s", ticker, strategy, e)

    return result
