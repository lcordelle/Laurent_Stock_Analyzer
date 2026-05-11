"""
Trading Strategy Chart
Visualizes entry, stop loss, take profit targets with risk/reward zones
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.visualizations import normalize_primary_stance


def create_trading_strategy_chart(data, trading_signals=None, intrinsic_value=None, metrics=None, score=None):
    """
    Create a comprehensive trading strategy chart showing:
    - Entry point (BUY/SELL signal)
    - Stop Loss level
    - Multiple Take Profit targets (TP1, TP2, TP3)
    - Risk zone (red) and Profit zone (green)
    - Rationale annotations based on data points
    """
    if not data:
        return None
    
    hist = data.get('history')
    if hist is None or len(hist) == 0:
        return None
    
    ticker = data.get('ticker', 'Unknown')
    current_price = hist['Close'].iloc[-1] if len(hist) > 0 else 0
    
    if not trading_signals:
        # Calculate trading signals if not provided
        from utils.visualizations import calculate_trading_signals, calculate_vwap, calculate_support_resistance
        vwap = calculate_vwap(hist)
        support, resistance = calculate_support_resistance(hist)
        trading_signals = calculate_trading_signals(hist, intrinsic_value, metrics, score, vwap, support, resistance)
    
    if not trading_signals:
        return None
    
    fig = go.Figure()
    
    # Align with signal chart: same normalized primary_stance (never infer SELL from a bad else-branch)
    primary = normalize_primary_stance(trading_signals.get('primary_stance'))
    if primary == 'BUY':
        is_buy_strategy, is_sell_strategy = True, False
    elif primary == 'SELL':
        is_buy_strategy, is_sell_strategy = False, True
    else:
        is_buy_strategy, is_sell_strategy = False, False
    
    # Get entry price
    entry_price = current_price
    entry_date = hist.index[-1]
    entry_reason = "Current Market Price"
    
    if is_buy_strategy and trading_signals.get('buy_signals'):
        best_buy = min(trading_signals['buy_signals'], key=lambda x: x['price'])
        entry_price = best_buy['price']
        entry_date = best_buy['date']
        entry_reason = best_buy.get('reason', 'Buy Signal')
    elif is_sell_strategy and trading_signals.get('sell_signals'):
        best_sell = max(trading_signals['sell_signals'], key=lambda x: x['price'])
        entry_price = best_sell['price']
        entry_date = best_sell['date']
        entry_reason = best_sell.get('reason', 'Sell Signal')
    elif trading_signals.get('optimal_entry'):
        entry_price = trading_signals['optimal_entry']['price']
        entry_reason = trading_signals['optimal_entry'].get('reason', 'Optimal Entry')
    
    # Get stop loss
    stop_loss_price = None
    if trading_signals.get('stop_loss'):
        stop_loss_price = trading_signals['stop_loss']['price']
    else:
        # Calculate stop loss based on strategy type
        from utils.visualizations import calculate_support_resistance
        support, resistance = calculate_support_resistance(hist)
        
        if is_buy_strategy and support:
            stop_loss_price = support * 0.98  # Just below support
        elif is_sell_strategy and resistance:
            stop_loss_price = resistance * 1.02  # Just above resistance
        elif not is_buy_strategy and not is_sell_strategy:
            stop_loss_price = entry_price * 0.97  # HOLD: light reference only
        else:
            # Default: 5% stop loss
            if is_buy_strategy:
                stop_loss_price = entry_price * 0.95
            else:
                stop_loss_price = entry_price * 1.05
    
    # Get take profit targets
    take_profit_targets = []
    if trading_signals.get('take_profit'):
        take_profit_targets = trading_signals['take_profit']
    else:
        # Create default TP targets if not available
        if is_buy_strategy:
            # For buy: TP1 = +5%, TP2 = +10%, TP3 = +15% or fair value
            tp1 = entry_price * 1.05
            tp2 = entry_price * 1.10
            tp3 = intrinsic_value if intrinsic_value and intrinsic_value > entry_price else entry_price * 1.15
            
            take_profit_targets = [
                {'price': tp1, 'label': f'TP1: ${tp1:.2f} (+5%)', 'target': '5%'},
                {'price': tp2, 'label': f'TP2: ${tp2:.2f} (+10%)', 'target': '10%'},
                {'price': tp3, 'label': f'TP3: ${tp3:.2f} (+15% or Fair Value)', 'target': '15%'}
            ]
        elif is_sell_strategy:
            # For sell: TP1 = -5%, TP2 = -10%, TP3 = -15% or support
            tp1 = entry_price * 0.95
            tp2 = entry_price * 0.90
            tp3 = support if support and support < entry_price else entry_price * 0.85
            
            take_profit_targets = [
                {'price': tp1, 'label': f'TP1: ${tp1:.2f} (-5%)', 'target': '5%'},
                {'price': tp2, 'label': f'TP2: ${tp2:.2f} (-10%)', 'target': '10%'},
                {'price': tp3, 'label': f'TP3: ${tp3:.2f} (-15% or Support)', 'target': '15%'}
            ]
        elif not is_buy_strategy and not is_sell_strategy:
            take_profit_targets = [
                {'price': entry_price * 1.03, 'label': f'Upside ref: ${entry_price * 1.03:.2f}', 'target': 'ref'},
                {'price': entry_price * 0.97, 'label': f'Downside ref: ${entry_price * 0.97:.2f}', 'target': 'ref'},
            ]
    
    # Sort TP targets (ascending for buy, descending for sell)
    if take_profit_targets:
        take_profit_targets.sort(key=lambda x: x['price'], reverse=is_sell_strategy)
    
    # Calculate risk/reward zones
    dates = hist.index
    entry_date_idx = len(dates) - 1
    
    # Add candlestick chart first (background)
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # Risk / reward bands only when primary is directional (HOLD = no shaded zones)
    if stop_loss_price and (is_buy_strategy or is_sell_strategy):
        if is_buy_strategy:
            risk_zone_top = entry_price
            risk_zone_bottom = stop_loss_price
        else:
            risk_zone_top = stop_loss_price
            risk_zone_bottom = entry_price
        fig.add_shape(
            type="rect",
            x0=dates[0],
            y0=risk_zone_bottom,
            x1=dates[-1],
            y1=risk_zone_top,
            fillcolor="rgba(239, 68, 68, 0.2)",
            line=dict(width=0),
            layer="below"
        )

    if take_profit_targets and (is_buy_strategy or is_sell_strategy):
        tp3_price = take_profit_targets[-1]['price']
        if is_buy_strategy:
            profit_zone_bottom = entry_price
            profit_zone_top = tp3_price
        else:
            profit_zone_top = entry_price
            profit_zone_bottom = tp3_price
        fig.add_shape(
            type="rect",
            x0=dates[0],
            y0=profit_zone_bottom,
            x1=dates[-1],
            y1=profit_zone_top,
            fillcolor="rgba(16, 185, 129, 0.15)",
            line=dict(width=0),
            layer="below"
        )
    
    # Entry line colors follow primary stance (same as pro signal chart)
    if primary == 'HOLD':
        signal_text = "HOLD"
        signal_color = "#64748b"
        sym = 'circle'
    elif primary == 'BUY':
        signal_text = "BUY"
        signal_color = "#3b82f6"
        sym = 'triangle-up'
    elif primary == 'SELL':
        signal_text = "SELL"
        signal_color = "#ef4444"
        sym = 'triangle-down'
    else:
        signal_text = "HOLD"
        signal_color = "#64748b"
        sym = 'circle'

    # Add Entry line and annotation - position on left, bottom with offset
    fig.add_hline(
        y=entry_price,
        line_dash="solid",
        line_color=signal_color,
        line_width=3,
        annotation_text=f"Entry / {signal_text}: ${entry_price:.2f}",
        annotation_position="left",
        annotation_yanchor="bottom",
        annotation_y=0,
        annotation_x=0.05,  # Position away from edge
        annotation_font=dict(size=12, color=signal_color, family="Arial Black"),
        annotation_bgcolor="rgba(255, 255, 255, 0.95)",
        annotation_bordercolor=signal_color,
        annotation_borderwidth=2,
        annotation_borderpad=4,
        opacity=1.0
    )
    
    # Add Entry signal marker (matches primary_stance, not conflicting raw flags)
    fig.add_trace(go.Scatter(
        x=[entry_date],
        y=[entry_price],
        mode='markers+text',
        name=signal_text,
        marker=dict(
            size=25,
            color=signal_color,
            symbol=sym,
            line=dict(width=4, color='white'),
            opacity=1.0
        ),
        text=[signal_text],
        textposition='top center',
        textfont=dict(size=16, color=signal_color, family='Arial Black'),
        showlegend=False,
        hovertemplate=f'<b>{signal_text} Entry</b><br>Price: ${entry_price:.2f}<br>Reason: {entry_reason}<extra></extra>'
    ))
    
    # Add Stop Loss line and annotation - position on right, top with offset
    if stop_loss_price:
        fig.add_hline(
            y=stop_loss_price,
            line_dash="solid",
            line_color="#ef4444",
            line_width=3,
            annotation_text=f"SL: ${stop_loss_price:.2f}",
            annotation_position="right",
            annotation_yanchor="top",
            annotation_y=0,
            annotation_x=0.95,  # Position away from edge
            annotation_font=dict(size=12, color="#ef4444", family="Arial Black"),
            annotation_bgcolor="rgba(255, 255, 255, 0.95)",
            annotation_bordercolor="#ef4444",
            annotation_borderwidth=2,
            annotation_borderpad=4,
            opacity=1.0
        )
        
        # Add stop loss marker
        fig.add_trace(go.Scatter(
            x=[entry_date],
            y=[stop_loss_price],
            mode='markers',
            name='Stop Loss',
            marker=dict(
                size=12,
                color='#ef4444',
                symbol='square',
                line=dict(width=2, color='white'),
                opacity=1.0
            ),
            showlegend=False,
            hovertemplate=f'<b>Stop Loss</b><br>Price: ${stop_loss_price:.2f}<extra></extra>'
        ))
    
    # Add Take Profit targets
    tp_colors = ['#10b981', '#059669', '#047857']  # Green shades
    for idx, tp in enumerate(take_profit_targets[:3]):  # Limit to 3 TPs
        tp_price = tp['price']
        tp_label = tp.get('label', f'TP{idx+1}')
        
        # Add TP line - stack vertically on right side
        fig.add_hline(
            y=tp_price,
            line_dash="solid",
            line_color=tp_colors[idx] if idx < len(tp_colors) else '#10b981',
            line_width=2,
            annotation_text=f"{tp_label.split(':')[0]}: ${tp_price:.2f}",
            annotation_position="right",
            annotation_yanchor="top",
            annotation_y=40 + (idx * 32),  # Increased spacing
            annotation_x=0.92,  # Position away from edge
            annotation_font=dict(
                size=11,
                color=tp_colors[idx] if idx < len(tp_colors) else '#10b981',
                family="Arial"
            ),
            annotation_bgcolor="rgba(255, 255, 255, 0.95)",
            annotation_bordercolor=tp_colors[idx] if idx < len(tp_colors) else '#10b981',
            annotation_borderwidth=1,
            annotation_borderpad=4,
            opacity=0.9
        )
        
        # Add TP marker
        fig.add_trace(go.Scatter(
            x=[entry_date],
            y=[tp_price],
            mode='markers',
            name=f'TP{idx+1}',
            marker=dict(
                size=10,
                color=tp_colors[idx] if idx < len(tp_colors) else '#10b981',
                symbol='diamond',
                line=dict(width=2, color='white'),
                opacity=1.0
            ),
            showlegend=False,
            hovertemplate=f'<b>{tp_label}</b><br>Price: ${tp_price:.2f}<extra></extra>'
        ))
    
    # Get support and resistance for rationale
    from utils.visualizations import calculate_support_resistance
    support, resistance = calculate_support_resistance(hist)
    
    # Add rationale annotation box
    rationale_text = _build_rationale_text(
        trading_signals,
        entry_price,
        stop_loss_price,
        take_profit_targets,
        is_buy_strategy,
        is_sell_strategy,
        intrinsic_value,
        support,
        resistance,
    )
    
    # Update layout
    prim_note = ""
    if trading_signals.get('has_conflicting_signals'):
        prim_note = " (conflicting rules resolved to primary stance)"
    fig.update_layout(
        title={
            'text': f'{ticker} — Trading strategy: {signal_text}{prim_note}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': signal_color}
        },
        yaxis_title='Price ($)',
        xaxis_title='Date',
        height=700,
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        annotations=[
            dict(
                x=0.02,
                y=0.98,
                xref="paper",
                yref="paper",
                text=rationale_text,
                showarrow=False,
                align="left",
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor=signal_color,
                borderwidth=3,
                borderpad=12,
                font=dict(size=11, color="#1f2937", family="Arial"),
                xanchor="left",
                yanchor="top"
            )
        ]
    )
    
    return fig

def _build_rationale_text(
    trading_signals,
    entry_price,
    stop_loss_price,
    take_profit_targets,
    is_buy_strategy,
    is_sell_strategy,
    intrinsic_value,
    support,
    resistance,
):
    """Build rationale text explaining the trading strategy"""
    rationale_parts = []
    primary = normalize_primary_stance(trading_signals.get('primary_stance'))
    rationale_parts.append(f"<b>STRATEGY RATIONALE (primary: {primary}):</b><br>")
    if trading_signals.get('primary_stance_reason'):
        rationale_parts.append(f"• {trading_signals['primary_stance_reason']}<br>")

    # Entry reason — use same side as primary stance
    if trading_signals.get('buy_signals') and is_buy_strategy:
        best_buy = min(trading_signals['buy_signals'], key=lambda x: x['price'])
        rationale_parts.append(f"• <b>Entry:</b> {best_buy.get('reason', 'Buy signal triggered')}<br>")
    elif trading_signals.get('sell_signals') and is_sell_strategy:
        best_sell = max(trading_signals['sell_signals'], key=lambda x: x['price'])
        rationale_parts.append(f"• <b>Entry:</b> {best_sell.get('reason', 'Sell signal triggered')}<br>")
    else:
        rationale_parts.append(f"• <b>Entry:</b> Spot / no primary directional edge — monitor levels.<br>")
    
    # Stop Loss rationale
    if stop_loss_price:
        risk_pct = abs((stop_loss_price - entry_price) / entry_price * 100)
        rationale_parts.append(f"• <b>Stop Loss:</b> ${stop_loss_price:.2f} ({risk_pct:.1f}% risk) - Limits downside<br>")
    
    # Take Profit rationale
    if take_profit_targets:
        tp1 = take_profit_targets[0]['price']
        tp3 = take_profit_targets[-1]['price']
        reward_pct = abs((tp3 - entry_price) / entry_price * 100)
        rationale_parts.append(f"• <b>Take Profit:</b> {len(take_profit_targets)} targets up to ${tp3:.2f} ({reward_pct:.1f}% potential gain)<br>")
    
    # Risk/Reward ratio
    if stop_loss_price and take_profit_targets:
        risk = abs(entry_price - stop_loss_price)
        reward = abs(take_profit_targets[-1]['price'] - entry_price)
        if risk > 0:
            rr_ratio = reward / risk
            rationale_parts.append(f"• <b>Risk/Reward:</b> 1:{rr_ratio:.2f} (Reward {rr_ratio:.1f}x the risk)<br>")
    
    # Technical levels
    if support:
        rationale_parts.append(f"• <b>Support:</b> ${support:.2f}<br>")
    if resistance:
        rationale_parts.append(f"• <b>Resistance:</b> ${resistance:.2f}<br>")
    if intrinsic_value:
        if primary == 'BUY':
            discount = ((intrinsic_value - entry_price) / entry_price * 100)
            rationale_parts.append(
                f"• <b>Fair Value:</b> ${intrinsic_value:.2f} ({abs(discount):.1f}% vs spot — discount lens)<br>"
            )
        elif primary == 'SELL':
            discount = ((entry_price - intrinsic_value) / intrinsic_value * 100)
            rationale_parts.append(
                f"• <b>Fair Value:</b> ${intrinsic_value:.2f} ({abs(discount):.1f}% vs spot — premium lens)<br>"
            )
        else:
            rationale_parts.append(f"• <b>Fair Value:</b> ${intrinsic_value:.2f} (reference only in HOLD)<br>")
    
    # Confidence
    confidence = trading_signals.get('confidence_score', 0)
    confidence_level = trading_signals.get('confidence_level', 'Low')
    rationale_parts.append(f"• <b>Confidence:</b> {confidence_level} ({confidence:.0f}/100)<br>")
    
    return "".join(rationale_parts)
