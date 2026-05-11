"""
AI Price Predictor — weighted signal aggregation across 9 technical indicators
"""

import numpy as np


class AIPredictor:

    WEIGHTS = {
        'MACD':       0.20,
        'RSI':        0.15,
        'Ichimoku':   0.15,
        'ADX':        0.10,
        'Bollinger':  0.10,
        'Stochastic': 0.10,
        'SMA':        0.10,
        'Volume':     0.05,
        'VF_Score':   0.05,
    }

    def predict(self, hist, metrics, score, forecast):
        signals = {}

        signals['RSI']        = self._signal_rsi(hist)
        signals['MACD']       = self._signal_macd(hist)
        signals['Bollinger']  = self._signal_bollinger(hist)
        signals['Stochastic'] = self._signal_stochastic(hist)
        signals['ADX']        = self._signal_adx(hist)
        signals['Ichimoku']   = self._signal_ichimoku(hist)
        signals['SMA']        = self._signal_sma(hist)
        signals['Volume']     = self._signal_volume(hist)
        signals['VF_Score']   = self._signal_vf_score(score)

        weighted_sum = sum(
            signals[k]['raw_score'] * self.WEIGHTS[k]
            for k in self.WEIGHTS
        )

        bull_score = (weighted_sum + 1.0) / 2.0 * 100
        confidence = abs(weighted_sum) * 100

        if weighted_sum > 0.15:
            direction = 'BULL'
        elif weighted_sum < -0.15:
            direction = 'BEAR'
        else:
            direction = 'NEUTRAL'

        sign = 1 if direction == 'BULL' else (-1 if direction == 'BEAR' else 0)

        current = float(hist['Close'].iloc[-1])

        daily_vol = hist['Close'].pct_change().dropna().std()
        if np.isnan(daily_vol) or daily_vol == 0:
            daily_vol = 0.01
        sigma_5d = daily_vol * np.sqrt(5)

        conservative = current * (1 + sign * sigma_5d)
        base         = current * (1 + sign * 2 * sigma_5d)
        aggressive   = float(forecast.get('forecast_price', current * (1 + sign * 3 * sigma_5d)))

        atr_series = (hist['High'] - hist['Low']).rolling(14).mean()
        atr = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else current * 0.02

        entry     = current
        stop_loss = entry - sign * 2 * atr
        tp1       = entry + sign * 1 * atr
        tp2       = base
        tp3       = aggressive

        risk   = abs(entry - stop_loss)
        reward = abs(tp2 - entry)
        risk_reward = reward / risk if risk > 0 else 0.0

        volatility_pct = daily_vol * np.sqrt(252) * 100

        return {
            'direction':      direction,
            'confidence':     round(confidence, 1),
            'bull_score':     round(bull_score, 1),
            'weighted_sum':   round(weighted_sum, 4),
            'signals':        signals,
            'price_targets': {
                'current':      round(current, 2),
                'conservative': round(conservative, 2),
                'base':         round(base, 2),
                'aggressive':   round(aggressive, 2),
            },
            'entry':          round(entry, 2),
            'stop_loss':      round(stop_loss, 2),
            'tp1':            round(tp1, 2),
            'tp2':            round(tp2, 2),
            'tp3':            round(tp3, 2),
            'risk_reward':    round(risk_reward, 2),
            'time_horizon':   '5-day',
            'volatility_pct': round(volatility_pct, 1),
        }

    # ── Signal extractors ────────────────────────────────────────────────────

    def _make_signal(self, raw_score, value, weight_key):
        raw_score = float(np.clip(raw_score, -1.0, 1.0))
        return {
            'raw_score': round(raw_score, 4),
            'signal':    self._label_signal(raw_score),
            'value':     round(float(value), 2) if not np.isnan(float(value)) else 0.0,
            'weight':    self.WEIGHTS[weight_key],
        }

    def _label_signal(self, raw_score):
        if raw_score > 0.2:
            return 'bullish'
        if raw_score < -0.2:
            return 'bearish'
        return 'neutral'

    def _signal_rsi(self, hist):
        try:
            rsi = float(hist['RSI'].iloc[-1])
            if np.isnan(rsi):
                return self._make_signal(0.0, 0.0, 'RSI')
            if rsi < 30:
                score = 1.0
            elif rsi > 70:
                score = -1.0
            else:
                score = (50 - rsi) / 20.0
            return self._make_signal(score, rsi, 'RSI')
        except Exception:
            return self._make_signal(0.0, 0.0, 'RSI')

    def _signal_macd(self, hist):
        try:
            macd   = float(hist['MACD'].iloc[-1])
            signal = float(hist['Signal'].iloc[-1])
            if np.isnan(macd) or np.isnan(signal):
                return self._make_signal(0.0, 0.0, 'MACD')
            diff = macd - signal
            macd_std = float(hist['MACD'].rolling(20).std().iloc[-1])
            if np.isnan(macd_std) or macd_std == 0:
                raw = 1.0 if diff > 0 else (-1.0 if diff < 0 else 0.0)
            else:
                raw = diff / macd_std
            return self._make_signal(raw, macd, 'MACD')
        except Exception:
            return self._make_signal(0.0, 0.0, 'MACD')

    def _signal_bollinger(self, hist):
        try:
            close = float(hist['Close'].iloc[-1])
            upper = float(hist['BB_Upper'].iloc[-1])
            lower = float(hist['BB_Lower'].iloc[-1])
            if any(np.isnan(v) for v in [close, upper, lower]):
                return self._make_signal(0.0, 0.0, 'Bollinger')
            band_width = upper - lower
            if band_width < 1e-9:
                return self._make_signal(0.0, close, 'Bollinger')
            position = (close - lower) / band_width
            score = 1.0 - 2.0 * position
            return self._make_signal(score, close, 'Bollinger')
        except Exception:
            return self._make_signal(0.0, 0.0, 'Bollinger')

    def _signal_stochastic(self, hist):
        try:
            k = float(hist['Stoch_K'].iloc[-1])
            d = float(hist['Stoch_D'].iloc[-1])
            if np.isnan(k):
                return self._make_signal(0.0, 0.0, 'Stochastic')
            if k < 20:
                score = 1.0
            elif k > 80:
                score = -1.0
            else:
                score = (50 - k) / 30.0
            if len(hist) >= 2 and not np.isnan(d):
                k_prev = float(hist['Stoch_K'].iloc[-2])
                d_prev = float(hist['Stoch_D'].iloc[-2])
                if not np.isnan(k_prev) and not np.isnan(d_prev):
                    if k > d and k_prev <= d_prev:
                        score += 0.2
                    elif k < d and k_prev >= d_prev:
                        score -= 0.2
            return self._make_signal(score, k, 'Stochastic')
        except Exception:
            return self._make_signal(0.0, 0.0, 'Stochastic')

    def _signal_adx(self, hist):
        try:
            adx    = float(hist['ADX'].iloc[-1])
            di_pos = float(hist['DI_Plus'].iloc[-1])
            di_neg = float(hist['DI_Minus'].iloc[-1])
            if any(np.isnan(v) for v in [adx, di_pos, di_neg]):
                return self._make_signal(0.0, 0.0, 'ADX')
            direction = 1.0 if di_pos > di_neg else -1.0
            if adx > 25:
                score = direction
            elif adx >= 20:
                score = direction * (adx - 20) / 5.0
            else:
                score = 0.0
            return self._make_signal(score, adx, 'ADX')
        except Exception:
            return self._make_signal(0.0, 0.0, 'ADX')

    def _signal_ichimoku(self, hist):
        try:
            close = float(hist['Close'].iloc[-1])
            span_a_series = hist['Ichimoku_Senkou_A'].dropna()
            span_b_series = hist['Ichimoku_Senkou_B'].dropna()
            if span_a_series.empty or span_b_series.empty:
                return self._make_signal(0.0, 0.0, 'Ichimoku')
            span_a = float(span_a_series.iloc[-1])
            span_b = float(span_b_series.iloc[-1])
            if np.isnan(span_a) or np.isnan(span_b):
                return self._make_signal(0.0, 0.0, 'Ichimoku')
            cloud_top = max(span_a, span_b)
            cloud_bot = min(span_a, span_b)
            if close > cloud_top:
                score = 1.0
            elif close < cloud_bot:
                score = -1.0
            else:
                width = cloud_top - cloud_bot
                score = (close - cloud_bot) / width * 2.0 - 1.0 if width > 1e-9 else 0.0
            return self._make_signal(score, close, 'Ichimoku')
        except Exception:
            return self._make_signal(0.0, 0.0, 'Ichimoku')

    def _signal_sma(self, hist):
        try:
            close = float(hist['Close'].iloc[-1])
            sma20  = hist['SMA_20'].dropna()
            sma50  = hist['SMA_50'].dropna()
            sma200 = hist['SMA_200'].dropna()
            available = []
            for sma_s, name in [(sma20, 'SMA_20'), (sma50, 'SMA_50'), (sma200, 'SMA_200')]:
                if not sma_s.empty:
                    val = float(sma_s.iloc[-1])
                    if not np.isnan(val):
                        available.append(1.0 if close > val else -1.0)
            if not available:
                return self._make_signal(0.0, 0.0, 'SMA')
            per_component = 1.0 / len(available)
            score = sum(v * per_component for v in available)
            return self._make_signal(score, close, 'SMA')
        except Exception:
            return self._make_signal(0.0, 0.0, 'SMA')

    def _signal_volume(self, hist):
        try:
            if len(hist) < 21:
                return self._make_signal(0.0, 0.0, 'Volume')
            vol_20d = float(hist['Volume'].iloc[-21:-1].mean())
            vol_5d  = float(hist['Volume'].iloc[-6:-1].mean())
            if vol_20d == 0 or np.isnan(vol_20d) or np.isnan(vol_5d):
                return self._make_signal(0.0, 0.0, 'Volume')
            vol_ratio = vol_5d / vol_20d
            close_now = float(hist['Close'].iloc[-1])
            close_6d  = float(hist['Close'].iloc[-6])
            direction = 1.0 if close_now > close_6d else -1.0
            if vol_ratio <= 1.2:
                raw = direction * min(vol_ratio - 1.0, 0.3)
            else:
                raw = direction * min(vol_ratio - 1.0, 1.0)
            return self._make_signal(raw, vol_ratio, 'Volume')
        except Exception:
            return self._make_signal(0.0, 0.0, 'Volume')

    def _signal_vf_score(self, score):
        try:
            total = float(score.get('total_score', 50))
            raw = (total - 50.0) / 50.0
            return self._make_signal(raw, total, 'VF_Score')
        except Exception:
            return self._make_signal(0.0, 50.0, 'VF_Score')
