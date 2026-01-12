"""
Enhanced Metric Display with Color Coding and Explanations
Provides color-coded metrics with helpful explanations
"""

import streamlit as st

# Metric definitions with explanations and thresholds
METRIC_INFO = {
    # Valuation Metrics
    "P/E Ratio": {
        "good_threshold": 15,
        "bad_threshold": 25,
        "explanation": "Price-to-Earnings ratio: Measures how expensive a stock is relative to earnings. Lower is generally better (under 15 is excellent, 15-25 is reasonable, over 25 may be overvalued).",
        "inverse": False  # Lower is better
    },
    "Forward P/E": {
        "good_threshold": 15,
        "bad_threshold": 25,
        "explanation": "Forward P/E: Based on projected future earnings. Lower values suggest better value. Compare with current P/E to see if earnings are expected to grow.",
        "inverse": False
    },
    "PEG Ratio": {
        "good_threshold": 1.0,
        "bad_threshold": 2.0,
        "explanation": "Price/Earnings to Growth: Adjusts P/E for growth rate. Under 1.0 is excellent (undervalued), 1.0-2.0 is reasonable, over 2.0 may be overvalued.",
        "inverse": False
    },
    "Price to Book": {
        "good_threshold": 1.5,
        "bad_threshold": 3.0,
        "explanation": "Price-to-Book ratio: Compares stock price to company's book value. Under 1.5 is excellent, 1.5-3.0 is reasonable, over 3.0 may indicate overvaluation.",
        "inverse": False
    },
    
    # Profitability Metrics
    "Gross Margin": {
        "good_threshold": 30,
        "bad_threshold": 15,
        "explanation": "Gross Margin %: Percentage of revenue remaining after cost of goods sold. Higher is better. Over 30% is excellent, 15-30% is good, under 15% may indicate pricing pressure.",
        "inverse": True  # Higher is better
    },
    "Operating Margin": {
        "good_threshold": 15,
        "bad_threshold": 5,
        "explanation": "Operating Margin %: Profitability after operating expenses. Over 15% is excellent, 5-15% is good, under 5% may indicate operational inefficiency.",
        "inverse": True
    },
    "Profit Margin": {
        "good_threshold": 10,
        "bad_threshold": 3,
        "explanation": "Profit Margin %: Net income as % of revenue. Over 10% is excellent, 3-10% is good, under 3% may indicate thin margins.",
        "inverse": True
    },
    
    # Returns
    "ROE": {
        "good_threshold": 15,
        "bad_threshold": 8,
        "explanation": "Return on Equity: Measures how efficiently company uses shareholders' equity. Over 15% is excellent, 8-15% is good, under 8% may indicate inefficient use of capital.",
        "inverse": True
    },
    "ROA": {
        "good_threshold": 7,
        "bad_threshold": 3,
        "explanation": "Return on Assets: Measures how efficiently company uses assets to generate profit. Over 7% is excellent, 3-7% is good, under 3% may indicate poor asset utilization.",
        "inverse": True
    },
    "Dividend Yield": {
        "good_threshold": 2.0,
        "bad_threshold": 0.5,
        "explanation": "Dividend Yield %: Annual dividend as % of stock price. Higher yields provide income but may signal slower growth. 2-4% is typical for mature companies.",
        "inverse": False  # Context-dependent
    },
    
    # Growth
    "Revenue Growth": {
        "good_threshold": 10,
        "bad_threshold": 0,
        "explanation": "Revenue Growth %: Year-over-year revenue increase. Over 10% is excellent growth, 0-10% is moderate, negative indicates declining sales.",
        "inverse": True
    },
    "Earnings Growth": {
        "good_threshold": 15,
        "bad_threshold": 0,
        "explanation": "Earnings Growth %: Year-over-year earnings increase. Over 15% is excellent, 0-15% is moderate, negative indicates declining profitability.",
        "inverse": True
    },
    
    # Financial Strength
    "Debt to Equity": {
        "good_threshold": 0.5,
        "bad_threshold": 1.0,
        "explanation": "Debt-to-Equity: Ratio of debt to shareholders' equity. Under 0.5 is excellent (low debt), 0.5-1.0 is reasonable, over 1.0 may indicate high financial risk.",
        "inverse": False
    },
    "Current Ratio": {
        "good_threshold": 1.5,
        "bad_threshold": 1.0,
        "explanation": "Current Ratio: Ability to pay short-term debts. Over 1.5 is excellent (good liquidity), 1.0-1.5 is adequate, under 1.0 may indicate liquidity risk.",
        "inverse": True
    },
    "Quick Ratio": {
        "good_threshold": 1.0,
        "bad_threshold": 0.5,
        "explanation": "Quick Ratio: Liquidity without inventory. Over 1.0 is excellent, 0.5-1.0 is adequate, under 0.5 may indicate difficulty meeting short-term obligations.",
        "inverse": True
    },
    
    # Risk Metrics
    "Beta": {
        "good_threshold": 1.0,
        "bad_threshold": 1.5,
        "explanation": "Beta: Stock's volatility vs market. 1.0 = moves with market, <1.0 = less volatile (safer), >1.0 = more volatile (riskier). Lower beta = less risk.",
        "inverse": False
    },
    "Volatility": {
        "good_threshold": 20,
        "bad_threshold": 40,
        "explanation": "Volatility %: Annual price volatility. Under 20% is low volatility (stable), 20-40% is moderate, over 40% is high volatility (risky).",
        "inverse": False
    },
    "Sharpe Ratio": {
        "good_threshold": 1.0,
        "bad_threshold": 0.5,
        "explanation": "Sharpe Ratio: Risk-adjusted return. Over 1.0 is excellent, 0.5-1.0 is good, under 0.5 indicates poor risk-adjusted returns.",
        "inverse": True
    },
    "Max Drawdown": {
        "good_threshold": -15,
        "bad_threshold": -30,
        "explanation": "Max Drawdown %: Largest peak-to-trough decline. Under -15% is good, -15% to -30% is moderate, over -30% indicates high downside risk.",
        "inverse": True  # Less negative is better
    },
    
    # Technical Indicators
    "RSI": {
        "good_threshold": 30,
        "bad_threshold": 70,
        "explanation": "RSI (14): Relative Strength Index. 30-70 is neutral range. Under 30 = oversold (potential buy), over 70 = overbought (potential sell).",
        "inverse": False,
        "range": (0, 100)
    },
    "MACD": {
        "good_threshold": 0,
        "bad_threshold": 0,
        "explanation": "MACD: Moving Average Convergence Divergence. Positive = bullish momentum, negative = bearish. Above signal line = buy signal, below = sell signal.",
        "inverse": False,
        "custom": True
    },
}

def get_metric_color(value, metric_name, inverse=False, custom_range=None):
    """Determine color for metric based on value"""
    if metric_name not in METRIC_INFO:
        return "normal"
    
    info = METRIC_INFO[metric_name]
    good_thresh = info.get("good_threshold", 0)
    bad_thresh = info.get("bad_threshold", 0)
    is_inverse = info.get("inverse", inverse)
    
    if custom_range:
        # For metrics with specific ranges (like RSI)
        if metric_name == "RSI":
            if value < 30:
                return "normal"  # Oversold - neutral
            elif value > 70:
                return "normal"  # Overbought - neutral
            else:
                return "normal"
        return "normal"
    
    try:
        value_float = float(value) if isinstance(value, (int, float, str)) else 0
    except:
        return "normal"
    
    if is_inverse:
        # Higher is better
        if value_float >= good_thresh:
            return "normal"  # Green
        elif value_float >= bad_thresh:
            return "off"  # Yellow
        else:
            return "inverse"  # Red
    else:
        # Lower is better
        if value_float <= good_thresh:
            return "normal"  # Green
        elif value_float <= bad_thresh:
            return "off"  # Yellow
        else:
            return "inverse"  # Red

def display_enhanced_metric(label, value, delta=None, help_text=None, metric_name=None):
    """
    Display a metric with color coding and explanation
    
    Args:
        label: Metric label
        value: Metric value (can be string or number)
        delta: Optional delta value for st.metric
        help_text: Optional custom help text (overrides auto-explanation)
        metric_name: Key name in METRIC_INFO for auto-explanation
    """
    # Try to get metric name from label if not provided
    if not metric_name:
        metric_name = label.replace("'s", "").replace(" ", "").replace("/", " to ")
        for key in METRIC_INFO.keys():
            if key.lower() in label.lower() or label.lower() in key.lower():
                metric_name = key
                break
    
    # Get explanation
    explanation = help_text
    if not explanation and metric_name in METRIC_INFO:
        explanation = METRIC_INFO[metric_name].get("explanation", "")
    
    # Determine color based on value
    try:
        # Try to extract numeric value
        if isinstance(value, str):
            # Remove currency symbols and percentage
            numeric_value = value.replace("$", "").replace("%", "").replace(",", "").strip()
            try:
                numeric_value = float(numeric_value)
            except:
                numeric_value = None
        else:
            numeric_value = value
        
        if numeric_value is not None:
            color = get_metric_color(numeric_value, metric_name)
        else:
            color = "normal"
    except:
        color = "normal"
    
    # Display metric with color styling
    if color == "normal":
        delta_color = "normal"  # Green for good values
    elif color == "off":
        delta_color = "off"  # Yellow for moderate values
    else:
        delta_color = "inverse"  # Red for bad values
    
    # Use st.metric with delta if provided
    if delta is not None:
        st.metric(label, value, delta=delta, delta_color=delta_color)
    else:
        # Use st.metric with appropriate delta color indicator
        # Create a visual indicator based on color
        if color == "normal":
            indicator = "✅"
        elif color == "off":
            indicator = "⚠️"
        else:
            indicator = "❌"
        
        # Use st.metric with a subtle delta if we want to show color
        st.metric(label, value)
        # Add color border using custom HTML
        st.markdown(
            f'<div style="border-left: 4px solid {"#4CAF50" if color == "normal" else "#FFA726" if color == "off" else "#EF5350"}; padding-left: 0.5rem; margin-top: -0.5rem; margin-bottom: 0.5rem;"></div>',
            unsafe_allow_html=True
        )
    
    # Display explanation below metric
    if explanation:
        st.caption(explanation)

