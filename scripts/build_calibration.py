"""Build data/calibration.json by pooling the conviction model over S&P 100 history.
Throttled + per-ticker cached + resumable to tolerate yfinance rate-limits.
Run: python3 scripts/build_calibration.py [--limit N]"""
import argparse
import json
import os
import sys
import time

import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.decision_engine import HORIZON_PROFILES  # noqa: E402
from utils.calibration import (SP100, observations_for_history, bucketize,  # noqa: E402
                               conviction_percentiles)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CACHE = os.path.join(_ROOT, "data", "cal_cache")
_OUT = os.path.join(_ROOT, "data", "calibration.json")


def _load_ticker(ticker: str):
    os.makedirs(_CACHE, exist_ok=True)
    cache = os.path.join(_CACHE, f"{ticker}.csv")
    if os.path.exists(cache):
        try:
            return pd.read_csv(cache, index_col=0, parse_dates=True)
        except Exception:
            pass
    for attempt in range(3):
        try:
            h = yf.Ticker(ticker).history(period="5y")
            if h is not None and not h.empty:
                h.to_csv(cache)
                return h
        except Exception as e:
            print(f"  {ticker} attempt {attempt+1} failed: {e}")
        time.sleep(2 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="limit universe (testing)")
    args = ap.parse_args()
    universe = SP100[: args.limit] if args.limit else SP100

    vix = None
    try:
        vh = yf.Ticker("^VIX").history(period="5y")
        if vh is not None and not vh.empty:
            vix = vh["Close"]
            vix.index = vix.index.tz_localize(None) if vix.index.tz is not None else vix.index
    except Exception as e:
        print(f"VIX fetch failed ({e}); regimes will be Unknown")

    horizons_obs = {k: [] for k in HORIZON_PROFILES}
    covered, failed = 0, []
    for i, t in enumerate(universe, 1):
        print(f"[{i}/{len(universe)}] {t}")
        h = _load_ticker(t)
        if h is None or h.empty:
            failed.append(t); continue
        h.index = h.index.tz_localize(None) if getattr(h.index, "tz", None) is not None else h.index
        for key, prof in HORIZON_PROFILES.items():
            horizons_obs[key].extend(observations_for_history(h, vix, prof["window"], prof["weights"]))
        covered += 1
        time.sleep(0.5)  # throttle

    horizons = {}
    for key, prof in HORIZON_PROFILES.items():
        obs = horizons_obs[key]
        horizons[key] = {
            "horizon_days": prof["window"],
            "total_obs": len(obs),
            "buckets": bucketize(obs),
            "conviction_percentiles": conviction_percentiles(obs),
        }
    table = {
        "generated_at": time.strftime("%Y-%m-%d"),
        "universe": "SP100",
        "universe_size": covered,
        "failed": failed,
        "horizons": horizons,
    }
    os.makedirs(os.path.dirname(_OUT), exist_ok=True)
    with open(_OUT, "w") as f:
        json.dump(table, f, indent=2)
    print(f"Wrote {_OUT}: {covered} tickers, {len(failed)} failed, horizons " + ", ".join(f"{k}={len(horizons_obs[k])}" for k in horizons))


if __name__ == "__main__":
    main()
