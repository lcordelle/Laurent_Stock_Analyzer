"""
Trading Buy/Sell Buttons Component
Prominent buy/sell boxes with recommended prices
"""

import streamlit as st

def render_buy_sell_boxes(current_price, trading_signals=None, metrics=None):
    """
    Render prominent buy/sell boxes with recommended prices
    Similar to professional trading platforms
    """
    if not current_price or current_price <= 0:
        return
    
    # Calculate recommended buy and sell prices
    # Buy price (ask) - typically slightly above current for market orders
    # Sell price (bid) - typically slightly below current for market orders
    buy_price = current_price * 1.001  # Add small spread for buy
    sell_price = current_price * 0.999  # Subtract small spread for sell
    
    # Get optimal entry from trading signals if available
    if trading_signals:
        if trading_signals.get('optimal_entry'):
            buy_price = trading_signals['optimal_entry']['price']
        elif trading_signals.get('buy_signals'):
            # Use the best (lowest) buy signal price
            best_buy = min(trading_signals['buy_signals'], key=lambda x: x['price'])
            buy_price = best_buy['price']
        
        if trading_signals.get('sell_signals'):
            # Use the best (highest) sell signal price
            best_sell = max(trading_signals['sell_signals'], key=lambda x: x['price'])
            sell_price = best_sell['price']
        elif trading_signals.get('resistance_level'):
            # Use resistance as sell price
            sell_price = trading_signals['resistance_level']['price']
    
    # Ensure sell price is not higher than buy price (typical bid/ask)
    if sell_price > buy_price:
        # If sell is higher, adjust to create realistic spread
        mid_price = (buy_price + sell_price) / 2
        buy_price = mid_price * 1.001
        sell_price = mid_price * 0.999
    
    # Calculate spread
    spread = abs(buy_price - sell_price)
    
    # Round to 2 decimal places
    buy_price = round(buy_price, 2)
    sell_price = round(sell_price, 2)
    spread = round(spread, 2)
    
    # Render buy/sell boxes with professional styling
    st.markdown("""
    <style>
        .trading-buttons-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            margin: 2rem 0;
            padding: 0;
        }
        
        .trading-button {
            flex: 0 1 auto;
            min-width: 180px;
            padding: 2rem 2.5rem;
            border-radius: 16px;
            text-align: center;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .trading-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .trading-button:hover::before {
            left: 100%;
        }
        
        .trading-button:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
        }
        
        .trading-button:active {
            transform: translateY(-2px) scale(1.01);
        }
        
        .buy-button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
            color: white;
        }
        
        .buy-button:hover {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%);
        }
        
        .sell-button {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
            color: white;
        }
        
        .sell-button:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%);
        }
        
        .trading-label {
            font-size: 1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.75rem;
            opacity: 0.95;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .trading-price {
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0;
            font-family: 'Arial Black', 'Helvetica Neue', sans-serif;
            text-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
            letter-spacing: -0.02em;
        }
        
        .spread-indicator {
            font-size: 1rem;
            color: var(--text-primary);
            font-weight: 700;
            padding: 0.75rem 1.25rem;
            background: var(--bg-tertiary);
            border-radius: 10px;
            min-width: 80px;
            text-align: center;
            border: 2px solid var(--border-medium);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the buy/sell boxes HTML
    buy_sell_html = f"""
    <div class="trading-buttons-container">
        <div class="trading-button sell-button" onclick="alert('Sell order would be placed at ${sell_price:.2f}')">
            <div class="trading-label">SELL</div>
            <div class="trading-price">${sell_price:.2f}</div>
        </div>
        <div class="spread-indicator">
            {spread:.2f}
        </div>
        <div class="trading-button buy-button" onclick="alert('Buy order would be placed at ${buy_price:.2f}')">
            <div class="trading-label">BUY</div>
            <div class="trading-price">${buy_price:.2f}</div>
        </div>
    </div>
    """
    
    st.markdown(buy_sell_html, unsafe_allow_html=True)
