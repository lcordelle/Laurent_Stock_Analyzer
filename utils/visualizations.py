"""
Visualization Functions
Creates interactive charts and graphs for stock analysis
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def calculate_vwap(hist):
    """Calculate Volume Weighted Average Price"""
    if hist is None or len(hist) == 0 or 'Volume' not in hist.columns:
        return None
    
    typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
    vwap = (typical_price * hist['Volume']).cumsum() / hist['Volume'].cumsum()
    return vwap

def calculate_support_resistance(hist, window=20):
    """Calculate support and resistance levels"""
    if hist is None or len(hist) < window:
        return None, None
    
    # Use recent window to find support/resistance
    recent_highs = hist['High'].rolling(window=window).max()
    recent_lows = hist['Low'].rolling(window=window).min()
    
    # Find key levels (local maxima and minima)
    resistance = recent_highs.max()
    support = recent_lows.min()
    
    return support, resistance

def calculate_pivot_points(hist):
    """Calculate pivot points for trading"""
    if hist is None or len(hist) == 0:
        return None
    
    # Use most recent day's high, low, close
    high = hist['High'].iloc[-1]
    low = hist['Low'].iloc[-1]
    close = hist['Close'].iloc[-1]
    
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    
    return {
        'pivot': pivot,
        'r1': r1,
        'r2': r2,
        's1': s1,
        's2': s2
    }

def calculate_fair_value_tunnel(intrinsic_value, current_price, hist):
    """Calculate fair value tunnel with upper and lower bounds"""
    if intrinsic_value is None or intrinsic_value <= 0:
        return None, None, None
    
    # Fair value tunnel: ±15% around intrinsic value (adjustable)
    tunnel_width = 0.15  # 15% on each side
    
    upper_bound = intrinsic_value * (1 + tunnel_width)
    lower_bound = intrinsic_value * (1 - tunnel_width)
    fair_value = intrinsic_value
    
    # Create arrays for the entire historical period
    dates = hist.index
    upper_array = np.full(len(dates), upper_bound)
    lower_array = np.full(len(dates), lower_bound)
    fair_array = np.full(len(dates), fair_value)
    
    return fair_array, upper_array, lower_array

def identify_entry_exit_signals(hist, current_price, intrinsic_value, vwap):
    """Identify entry and exit signals based on price action"""
    if hist is None or len(hist) < 20:
        return []
    
    signals = []
    dates = hist.index
    
    # Entry signals: price below fair value and above support
    # Exit signals: price above fair value and near resistance
    
    if intrinsic_value and current_price:
        discount = ((intrinsic_value - current_price) / current_price) * 100
        
        # Strong buy signal: significantly undervalued
        if discount > 20:
            signals.append({
                'date': dates[-1],
                'price': current_price,
                'signal': 'Strong Buy',
                'type': 'entry',
                'reason': f'Undervalued by {discount:.1f}%'
            })
        # Buy signal: moderately undervalued
        elif discount > 10:
            signals.append({
                'date': dates[-1],
                'price': current_price,
                'signal': 'Buy',
                'type': 'entry',
                'reason': f'Undervalued by {discount:.1f}%'
            })
        # Sell signal: overvalued
        elif discount < -20:
            signals.append({
                'date': dates[-1],
                'price': current_price,
                'signal': 'Strong Sell',
                'type': 'exit',
                'reason': f'Overvalued by {abs(discount):.1f}%'
            })
        elif discount < -10:
            signals.append({
                'date': dates[-1],
                'price': current_price,
                'signal': 'Sell',
                'type': 'exit',
                'reason': f'Overvalued by {abs(discount):.1f}%'
            })
    
    return signals

def create_price_chart(data, intrinsic_value=None, metrics=None):
    """Create interactive price chart with professional trading features:
    - Fair market value tunnel
    - VWAP (Volume Weighted Average Price)
    - Support/Resistance levels
    - Pivot points
    - Entry/Exit signals
    - Moving averages
    - Bollinger Bands
    """
    if not data:
        return None
    
    hist = data.get('history')
    if hist is None or len(hist) == 0:
        return None
    
    ticker = data.get('ticker', 'Unknown')
    current_price = hist['Close'].iloc[-1] if len(hist) > 0 else 0
    
    fig = go.Figure()
    
    # Calculate professional indicators
    vwap = calculate_vwap(hist)
    support, resistance = calculate_support_resistance(hist)
    pivot_points = calculate_pivot_points(hist)
    
    # Fair value tunnel
    fair_value_line = None
    fair_value_upper = None
    fair_value_lower = None
    
    if intrinsic_value and intrinsic_value > 0:
        fair_value_line, fair_value_upper, fair_value_lower = calculate_fair_value_tunnel(
            intrinsic_value, current_price, hist
        )
    
    # Add fair value tunnel (shaded area) - add first so it's in the background
    if fair_value_upper is not None and fair_value_lower is not None:
        # Upper bound
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=fair_value_upper,
            mode='lines',
            name='Fair Value Upper',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        # Lower bound with fill
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=fair_value_lower,
            mode='lines',
            name='Fair Value Tunnel',
            fill='tonexty',
            fillcolor='rgba(102, 126, 234, 0.15)',
            line=dict(width=0, color='rgba(102, 126, 234, 0.3)'),
            showlegend=True,
            hovertemplate='Fair Value Range: $%{y:.2f}<extra></extra>'
        ))
        # Fair value line
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=fair_value_line,
            mode='lines',
            name='Fair Market Value',
            line=dict(color='#667eea', width=2, dash='dash'),
            hovertemplate='Fair Value: $%{y:.2f}<extra></extra>'
        ))
    
    # Add support and resistance levels
    if support and resistance:
        fig.add_hline(
            y=support,
            line_dash="dot",
            line_color="green",
            annotation_text=f"Support: ${support:.2f}",
            annotation_position="right",
            opacity=0.7
        )
        fig.add_hline(
            y=resistance,
            line_dash="dot",
            line_color="red",
            annotation_text=f"Resistance: ${resistance:.2f}",
            annotation_position="right",
            opacity=0.7
        )
    
    # Add pivot points
    if pivot_points:
        fig.add_hline(
            y=pivot_points['pivot'],
            line_dash="dashdot",
            line_color="gray",
            annotation_text=f"Pivot: ${pivot_points['pivot']:.2f}",
            annotation_position="right",
            opacity=0.6
        )
        fig.add_hline(
            y=pivot_points['r1'],
            line_dash="dot",
            line_color="orange",
            annotation_text=f"R1: ${pivot_points['r1']:.2f}",
            annotation_position="right",
            opacity=0.5
        )
        fig.add_hline(
            y=pivot_points['s1'],
            line_dash="dot",
            line_color="lightgreen",
            annotation_text=f"S1: ${pivot_points['s1']:.2f}",
            annotation_position="right",
            opacity=0.5
        )
    
    # Add VWAP
    if vwap is not None:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=vwap,
            mode='lines',
            name='VWAP',
            line=dict(color='purple', width=2),
            hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
        ))
    
    # Add Bollinger Bands if available
    if 'BB_Upper' in hist.columns and 'BB_Lower' in hist.columns:
        # Upper band
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['BB_Upper'],
            mode='lines',
            name='BB Upper',
            line=dict(width=1, color='rgba(200, 200, 200, 0.5)'),
            showlegend=False,
            hoverinfo='skip'
        ))
        # Lower band with fill
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['BB_Lower'],
            mode='lines',
            name='Bollinger Bands',
            fill='tonexty',
            fillcolor='rgba(200, 200, 200, 0.1)',
            line=dict(width=1, color='rgba(200, 200, 200, 0.5)'),
            showlegend=True,
            hovertemplate='BB Lower: $%{y:.2f}<extra></extra>'
        ))
    
    # Candlestick chart (on top)
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
    
    # Add moving averages if calculated
    if 'SMA_20' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['SMA_20'],
            name='SMA 20',
            line=dict(color='orange', width=1.5),
            hovertemplate='SMA 20: $%{y:.2f}<extra></extra>'
        ))
    if 'SMA_50' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['SMA_50'],
            name='SMA 50',
            line=dict(color='blue', width=1.5),
            hovertemplate='SMA 50: $%{y:.2f}<extra></extra>'
        ))
    if 'SMA_200' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['SMA_200'],
            name='SMA 200',
            line=dict(color='red', width=1.5),
            hovertemplate='SMA 200: $%{y:.2f}<extra></extra>'
        ))
    
    # Add instructional entry/exit signals with educational context
    if intrinsic_value:
        signals = identify_entry_exit_signals(hist, current_price, intrinsic_value, vwap)
        if signals:
            for signal in signals:
                color = '#2e7d32' if signal['type'] == 'entry' else '#c62828'
                symbol = 'triangle-up' if signal['type'] == 'entry' else 'triangle-down'
                
                # Create instructional label
                if signal['type'] == 'entry':
                    instruction = f"💡 BUY OPPORTUNITY<br>${signal['price']:.2f}<br><sub>{signal['reason']}</sub>"
                    explanation = f"<b>📚 Why Buy?</b><br>{signal['reason']}<br><br><b>💡 Action:</b> Consider entering a position at this price level. The stock appears undervalued relative to its fair market value."
                else:
                    instruction = f"⚠️ SELL SIGNAL<br>${signal['price']:.2f}<br><sub>{signal['reason']}</sub>"
                    explanation = f"<b>📚 Why Sell?</b><br>{signal['reason']}<br><br><b>💡 Action:</b> Consider taking profits or exiting positions. The stock appears overvalued relative to its fair market value."
                
                fig.add_trace(go.Scatter(
                    x=[signal['date']],
                    y=[signal['price']],
                    mode='markers+text',
                    name=signal['signal'],
                    marker=dict(
                        size=18,
                        color=color,
                        symbol=symbol,
                        line=dict(width=2.5, color='white'),
                        opacity=0.9
                    ),
                    text=[instruction.split('<br>')[0]],  # Just show the main label
                    textposition='top center' if signal['type'] == 'entry' else 'bottom center',
                    textfont=dict(size=11, color=color),
                    hovertemplate=explanation + f"<br><br><b>Price:</b> ${signal['price']:.2f}<extra></extra>"
                ))
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} Professional Trading Chart',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        height=600,
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_volume_chart(hist, ticker):
    """Create volume chart"""
    if hist is None or len(hist) == 0:
        return None
    
    fig = go.Figure()
    
    colors = ['red' if row['Close'] < row['Open'] else 'green' 
              for idx, row in hist.iterrows()]
    
    fig.add_trace(go.Bar(
        x=hist.index,
        y=hist['Volume'],
        marker_color=colors,
        name='Volume'
    ))
    
    fig.update_layout(
        title=f'{ticker} Trading Volume',
        yaxis_title='Volume',
        xaxis_title='Date',
        height=300,
        template='plotly_white'
    )
    
    return fig

def create_comparison_table(stocks_data, analyzer):
    """Create comparison table for multiple stocks with forecasts"""
    comparison_data = []
    
    for ticker, data in stocks_data.items():
        if data is None:
            continue
        
        metrics = analyzer.get_key_metrics(data)
        score = analyzer.calculate_score(data)
        
        # Calculate forecast if technical indicators are available
        forecast = None
        if len(data['history']) >= 20:
            # Ensure technical indicators are calculated
            if 'SMA_20' not in data['history'].columns:
                data['history'] = analyzer.calculate_technical_indicators(data['history'])
            forecast = analyzer.calculate_forecast(data, metrics, score)
        
        comparison_data.append({
            'Ticker': ticker,
            'Company': data['info'].get('longName', ticker),
            'Score': score['total_score'] if score else 0,
            'Price': metrics['Current Price'],
            'Forecast Price': forecast['forecast_price'] if forecast else None,
            'Forecast Change %': forecast['forecast_change_pct'] if forecast else None,
            'Probability': forecast['probability'] if forecast else None,
            'Forecast Type': forecast['forecast_type'] if forecast else 'N/A',
            'Market Cap': metrics['Market Cap'],
            'P/E Ratio': metrics['P/E Ratio'],
            'Gross Margin': metrics['Gross Margin'],
            'ROE': metrics['ROE'],
            'Revenue Growth': metrics['Revenue Growth'],
            'Debt/Equity': metrics['Debt to Equity'],
            'Dividend Yield': metrics['Dividend Yield']
        })
    
    return pd.DataFrame(comparison_data)

def create_score_visualization(score_data):
    """Create score breakdown visualization"""
    if not score_data:
        return None
    
    components = score_data['components']
    
    fig = go.Figure(go.Bar(
        x=list(components.keys()),
        y=list(components.values()),
        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        text=list(components.values()),
        textposition='auto',
    ))
    
    fig.update_layout(
        title=f'Score Breakdown (Total: {score_data["total_score"]}/100)',
        yaxis_title='Points',
        xaxis_title='Category',
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_score_breakdown_table(score_data, forecast_data=None):
    """Create a styled score breakdown table with color indicators"""
    import streamlit as st
    
    if not score_data:
        return None
    
    components = score_data['components']
    total_score = score_data['total_score']
    
    # Create table data
    table_data = []
    
    # Define max points for each category
    max_points = {
        'Gross Margin': 25,
        'ROE': 20,
        'FCF Margin': 20,
        'Valuation': 20,
        'Growth': 15
    }
    
    # Calculate percentage and status for each component
    for category, points in components.items():
        max_pts = max_points.get(category, 25)
        percentage = (points / max_pts * 100) if max_pts > 0 else 0
        
        # Determine status and color
        if percentage >= 80:
            status = "Excellent"
            color = "#00c853"  # Green
            indicator = "🟢"
        elif percentage >= 60:
            status = "Good"
            color = "#64dd17"  # Light Green
            indicator = "🟡"
        elif percentage >= 40:
            status = "Fair"
            color = "#ffa726"  # Orange
            indicator = "🟠"
        elif percentage >= 20:
            status = "Below Average"
            color = "#ff6f00"  # Dark Orange
            indicator = "🟠"
        else:
            status = "Poor"
            color = "#ff1744"  # Red
            indicator = "🔴"
        
        table_data.append({
            'Category': category,
            'Points': points,
            'Max Points': max_pts,
            'Percentage': percentage,
            'Status': status,
            'Indicator': indicator,
            'Color': color
        })
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Display with styling
    st.markdown(f"### 📊 Score Breakdown Table (Total Score: {total_score}/100)")
    
    # Create display dataframe with formatted values
    display_df = pd.DataFrame({
        'Category': df['Category'],
        'Status': df['Indicator'] + ' ' + df['Status'],
        'Points': df['Points'].astype(int),
        'Max Points': df['Max Points'],
        'Percentage': df['Percentage'].apply(lambda x: f"{x:.1f}%"),
        'Assessment': df['Status']
    })
    
    # Create a styled dataframe with color coding
    def highlight_row(row):
        """Highlight rows based on status"""
        colors = []
        status = row['Assessment']
        
        if status == 'Excellent':
            bg_color = '#e8f5e9'  # Light green
        elif status == 'Good':
            bg_color = '#fff9c4'  # Light yellow
        elif status == 'Fair':
            bg_color = '#ffe0b2'  # Light orange
        else:  # Below Average or Poor
            bg_color = '#ffebee'  # Light red
        
        return [f'background-color: {bg_color}'] * len(row)
    
    # Apply styling
    styled_df = display_df.style.apply(highlight_row, axis=1)\
        .set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#667eea'), ('color', 'white'), ('font-weight', 'bold')]},
            {'selector': 'tbody tr:hover', 'props': [('background-color', '#f5f5f5')]},
        ])\
        .format({'Points': '{:.0f}', 'Max Points': '{:.0f}'})
    
    # Display the styled dataframe
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Add forecast section if available
    if forecast_data:
        st.markdown("---")
        st.markdown("### 🔮 Price Forecast Analysis (Multi-Period)")
        
        current_price = forecast_data['current_price']
        forecast_type = forecast_data['forecast_type']
        trend = forecast_data['trend']
        
        # Check if multi-period forecast is available
        has_multi_period = 'forecasts_by_period' in forecast_data
        
        if has_multi_period:
            forecasts_by_period = forecast_data['forecasts_by_period']
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"${current_price:.2f}")
            
            with col2:
                forecast_1m = forecasts_by_period['1_month']
                st.metric(
                    "1 Month Forecast",
                    f"${forecast_1m['forecast_price']:.2f}",
                    delta=f"{forecast_1m['forecast_change_pct']:+.2f}%"
                )
            
            with col3:
                forecast_12m = forecasts_by_period['12_months']
                st.metric(
                    "12 Month Forecast",
                    f"${forecast_12m['forecast_price']:.2f}",
                    delta=f"{forecast_12m['forecast_change_pct']:+.2f}%"
                )
            
            with col4:
                st.metric("Forecast Type", forecast_type)
            
            # Create 12-month forecast chart
            st.markdown("#### 📈 12-Month Forecast Projection")
            
            import plotly.graph_objects as go
            from datetime import datetime, timedelta
            
            # Prepare data for chart
            periods = ['Current', '1 Month', '3 Months', '6 Months', '12 Months']
            forecast_prices = [current_price]
            upper_bounds = [current_price]
            lower_bounds = [current_price]
            
            period_order = ['1_month', '3_months', '6_months', '12_months']
            for period_key in period_order:
                period_data = forecasts_by_period[period_key]
                forecast_prices.append(period_data['forecast_price'])
                upper_bounds.append(period_data['upper_bound'])
                lower_bounds.append(period_data['lower_bound'])
            
            # Create figure
            fig = go.Figure()
            
            # Add confidence band (shaded area)
            fig.add_trace(go.Scatter(
                x=periods,
                y=upper_bounds,
                mode='lines',
                name='Upper Bound',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(
                x=periods,
                y=lower_bounds,
                mode='lines',
                name='Confidence Band',
                fill='tonexty',
                fillcolor='rgba(102, 126, 234, 0.2)',
                line=dict(width=0),
                hoverinfo='skip'
            ))
            
            # Add forecast line
            fig.add_trace(go.Scatter(
                x=periods,
                y=forecast_prices,
                mode='lines+markers',
                name='Forecast Price',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10, color='#667eea'),
                hovertemplate='<b>%{x}</b><br>Forecast: $%{y:.2f}<extra></extra>'
            ))
            
            # Add current price marker
            fig.add_trace(go.Scatter(
                x=['Current'],
                y=[current_price],
                mode='markers',
                name='Current Price',
                marker=dict(size=15, color='#00c853', symbol='circle'),
                hovertemplate='<b>Current Price</b><br>$%{y:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Price Forecast Over 12 Months',
                xaxis_title='Time Period',
                yaxis_title='Price ($)',
                hovermode='x unified',
                height=400,
                template='plotly_white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display detailed forecast table
            st.markdown("#### 📊 Detailed Forecast by Period")
            
            forecast_table_data = []
            for period_key, period_data in forecasts_by_period.items():
                period_name = period_key.replace('_', ' ').title()
                forecast_table_data.append({
                    'Period': period_name,
                    'Forecast Price': f"${period_data['forecast_price']:.2f}",
                    'Expected Change': f"{period_data['forecast_change_pct']:+.2f}%",
                    'Probability': f"{period_data['probability']:.1f}%",
                    'Confidence': f"{period_data['confidence']:.0f}%",
                    'Range': f"${period_data['lower_bound']:.2f} - ${period_data['upper_bound']:.2f}"
                })
            
            forecast_df = pd.DataFrame(forecast_table_data)
            st.dataframe(
                forecast_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Additional metrics
            st.markdown("#### 📉 Additional Forecast Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Annual Return Estimate", f"{forecast_data.get('annual_return_estimate', 0):+.2f}%")
            
            with col2:
                st.metric("Momentum (20-day)", f"{forecast_data['momentum']:+.2f}%")
            
            with col3:
                st.metric("Volatility (Annualized)", f"{forecast_data['volatility']:.2f}%")
        else:
            # Fallback to single forecast (backward compatibility)
            forecast_price = forecast_data['forecast_price']
            change_pct = forecast_data['forecast_change_pct']
            probability = forecast_data['probability']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"${current_price:.2f}")
            
            with col2:
                st.metric(
                    "Forecast Price (30 days)",
                    f"${forecast_price:.2f}",
                    delta=f"{change_pct:+.2f}%"
                )
            
            with col3:
                st.metric("Probability", f"{probability:.1f}%")
            
            with col4:
                st.metric("Trend", trend)
    
    return df

def create_financial_metrics_chart(metrics):
    """Create financial metrics comparison chart"""
    categories = ['Gross Margin', 'Operating Margin', 'Profit Margin', 'ROE', 'ROA']
    values = [
        metrics.get('Gross Margin', 0),
        metrics.get('Operating Margin', 0),
        metrics.get('Profit Margin', 0),
        metrics.get('ROE', 0),
        metrics.get('ROA', 0)
    ]
    
    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker_color='lightblue',
        text=[f'{v:.2f}%' for v in values],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Key Financial Ratios (%)',
        yaxis_title='Percentage',
        height=400,
        template='plotly_white'
    )
    
    return fig

def calculate_optimal_entry_price(hist, intrinsic_value, support, vwap, current_price):
    """Calculate optimal entry price suggestion based on multiple factors"""
    if hist is None or len(hist) < 20:
        return None
    
    entry_candidates = []
    
    # Entry candidate 1: Support level
    if support:
        entry_candidates.append({
            'price': support,
            'reason': 'Support Level',
            'confidence': 'High'
        })
    
    # Entry candidate 2: Below fair value
    if intrinsic_value and intrinsic_value > 0:
        if current_price < intrinsic_value * 0.95:  # 5% below fair value
            entry_candidates.append({
                'price': current_price,
                'reason': 'Below Fair Value',
                'confidence': 'High'
            })
        # Ideal entry: 10% below fair value
        ideal_entry = intrinsic_value * 0.90
        if ideal_entry > 0:
            entry_candidates.append({
                'price': ideal_entry,
                'reason': 'Ideal Entry (10% below Fair Value)',
                'confidence': 'Very High'
            })
    
    # Entry candidate 3: VWAP (if price is below)
    if vwap is not None:
        try:
            vwap_value = float(vwap.iloc[-1]) if hasattr(vwap, 'iloc') else float(vwap)
            if current_price < vwap_value:
                entry_candidates.append({
                    'price': vwap_value * 0.98,  # Slightly below VWAP
                    'reason': 'Below VWAP',
                    'confidence': 'Medium'
                })
        except:
            pass
    
    # Return best entry (lowest price with highest confidence)
    if entry_candidates:
        # Sort by confidence (Very High > High > Medium) then by price (lowest first)
        confidence_order = {'Very High': 3, 'High': 2, 'Medium': 1}
        best_entry = min(entry_candidates, 
                        key=lambda x: (-confidence_order.get(x['confidence'], 0), x['price']))
        return best_entry
    
    return None

def calculate_optimal_entry_price(hist, intrinsic_value, support, vwap, current_price):
    """Calculate optimal entry price suggestion based on multiple factors"""
    if hist is None or len(hist) < 20:
        return None
    
    entry_candidates = []
    
    # Entry candidate 1: Support level
    if support:
        entry_candidates.append({
            'price': support,
            'reason': 'Support Level',
            'confidence': 'High'
        })
    
    # Entry candidate 2: Below fair value
    if intrinsic_value and intrinsic_value > 0:
        if current_price < intrinsic_value * 0.95:  # 5% below fair value
            entry_candidates.append({
                'price': current_price,
                'reason': 'Below Fair Value',
                'confidence': 'High'
            })
        # Ideal entry: 10% below fair value
        ideal_entry = intrinsic_value * 0.90
        if ideal_entry > 0:
            entry_candidates.append({
                'price': ideal_entry,
                'reason': 'Ideal Entry (10% below Fair Value)',
                'confidence': 'Very High'
            })
    
    # Entry candidate 3: VWAP (if price is below)
    if vwap is not None:
        try:
            vwap_value = float(vwap.iloc[-1]) if hasattr(vwap, 'iloc') else float(vwap)
            if current_price < vwap_value:
                entry_candidates.append({
                    'price': vwap_value * 0.98,  # Slightly below VWAP
                    'reason': 'Below VWAP',
                    'confidence': 'Medium'
                })
        except:
            pass
    
    # Return best entry (lowest price with highest confidence)
    if entry_candidates:
        # Sort by confidence (Very High > High > Medium) then by price (lowest first)
        confidence_order = {'Very High': 3, 'High': 2, 'Medium': 1}
        best_entry = min(entry_candidates, 
                        key=lambda x: (-confidence_order.get(x['confidence'], 0), x['price']))
        return best_entry
    
    return None

def calculate_trading_signals(hist, intrinsic_value, metrics, score, vwap, support, resistance):
    """Calculate professional trading buy/sell signals with entry/exit points"""
    if hist is None or len(hist) < 20:
        return None
    
    current_price = hist['Close'].iloc[-1]
    signals = {
        'buy_signals': [],
        'sell_signals': [],
        'entry_points': [],
        'exit_points': [],
        'stop_loss': None,
        'take_profit': [],
        'optimal_entry': None,  # Add optimal entry suggestion
        'resistance_level': None  # Add resistance level
    }
    
    # Calculate technical indicators if not present
    if 'RSI' not in hist.columns:
        return None
    
    # Ensure scalar values for technical indicators
    latest_rsi = float(hist['RSI'].iloc[-1]) if not pd.isna(hist['RSI'].iloc[-1]) else 50.0
    latest_macd = float(hist['MACD'].iloc[-1]) if 'MACD' in hist.columns and not pd.isna(hist['MACD'].iloc[-1]) else 0.0
    latest_signal = float(hist['Signal'].iloc[-1]) if 'Signal' in hist.columns and not pd.isna(hist['Signal'].iloc[-1]) else 0.0
    
    # Get moving averages (ensure scalar values)
    sma_20 = float(hist['SMA_20'].iloc[-1]) if 'SMA_20' in hist.columns and not pd.isna(hist['SMA_20'].iloc[-1]) else float(current_price)
    sma_50 = float(hist['SMA_50'].iloc[-1]) if 'SMA_50' in hist.columns and not pd.isna(hist['SMA_50'].iloc[-1]) else float(current_price)
    sma_200 = float(hist['SMA_200'].iloc[-1]) if 'SMA_200' in hist.columns and not pd.isna(hist['SMA_200'].iloc[-1]) else float(current_price)
    
    # Calculate price momentum
    if len(hist) >= 20:
        price_20_days_ago = hist['Close'].iloc[-20]
        momentum = ((current_price - price_20_days_ago) / price_20_days_ago) * 100
    else:
        momentum = 0
    
    # Professional Trading Logic
    
    # 1. BUY SIGNALS (Entry Points)
    
    # Buy Signal 1: Undervalued + Technical Support
    if intrinsic_value and current_price < intrinsic_value * 0.90:  # 10% below fair value
        buy_price = current_price
        buy_reason = f"Undervalued: ${current_price:.2f} vs Fair Value ${intrinsic_value:.2f} ({((intrinsic_value - current_price)/current_price*100):.1f}% discount)"
        signals['buy_signals'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'reason': buy_reason,
            'confidence': 'High' if current_price < intrinsic_value * 0.85 else 'Medium',
            'type': 'Value Buy'
        })
        signals['entry_points'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'label': f'BUY: ${buy_price:.2f}',
            'type': 'entry'
        })
    
    # Buy Signal 2: RSI Oversold + Price at Support
    if latest_rsi < 30 and support and current_price <= support * 1.02:
        buy_price = support
        buy_reason = f"Oversold (RSI: {latest_rsi:.1f}) + Support Level: ${support:.2f}"
        signals['buy_signals'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'reason': buy_reason,
            'confidence': 'High',
            'type': 'Technical Buy'
        })
        signals['entry_points'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'label': f'BUY: ${buy_price:.2f}',
            'type': 'entry'
        })
    
    # Buy Signal 3: Golden Cross (SMA 20 crosses above SMA 50) + Above VWAP
    # Extract VWAP value (handle Series or scalar)
    vwap_value = None
    if vwap is not None:
        try:
            if hasattr(vwap, 'iloc'):
                vwap_value = float(vwap.iloc[-1]) if len(vwap) > 0 and not pd.isna(vwap.iloc[-1]) else None
            else:
                vwap_value = float(vwap) if not pd.isna(vwap) else None
        except:
            vwap_value = None
    
    if sma_20 > sma_50 and (vwap_value is None or current_price > vwap_value):
        buy_price = current_price
        buy_reason = f"Golden Cross (SMA 20 > SMA 50) + Above VWAP"
        signals['buy_signals'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'reason': buy_reason,
            'confidence': 'Medium',
            'type': 'Momentum Buy'
        })
        signals['entry_points'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'label': f'BUY: ${buy_price:.2f}',
            'type': 'entry'
        })
    
    # Buy Signal 4: MACD Bullish Crossover + Strong Fundamentals
    if latest_macd > latest_signal and score and score.get('total_score', 0) >= 60:
        buy_price = current_price
        buy_reason = f"MACD Bullish + Strong Fundamentals (Score: {score['total_score']}/100)"
        signals['buy_signals'].append({
            'price': buy_price,
            'date': hist.index[-1],
            'reason': buy_reason,
            'confidence': 'Medium',
            'type': 'Momentum Buy'
        })
        if not any(abs(e['price'] - buy_price) < 0.01 for e in signals['entry_points']):
            signals['entry_points'].append({
                'price': buy_price,
                'date': hist.index[-1],
                'label': f'BUY: ${buy_price:.2f}',
                'type': 'entry'
            })
    
    # 2. SELL SIGNALS (Exit Points)
    
    # Sell Signal 1: Overvalued + Technical Resistance
    if intrinsic_value and current_price > intrinsic_value * 1.10:  # 10% above fair value
        sell_price = current_price
        sell_reason = f"Overvalued: ${current_price:.2f} vs Fair Value ${intrinsic_value:.2f} ({((current_price - intrinsic_value)/intrinsic_value*100):.1f}% premium)"
        signals['sell_signals'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'reason': sell_reason,
            'confidence': 'High' if current_price > intrinsic_value * 1.15 else 'Medium',
            'type': 'Value Sell'
        })
        signals['exit_points'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'label': f'SELL: ${sell_price:.2f}',
            'type': 'exit'
        })
    
    # Sell Signal 2: RSI Overbought + Price at Resistance
    if latest_rsi > 70 and resistance and current_price >= resistance * 0.98:
        sell_price = resistance
        sell_reason = f"Overbought (RSI: {latest_rsi:.1f}) + Resistance Level: ${resistance:.2f}"
        signals['sell_signals'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'reason': sell_reason,
            'confidence': 'High',
            'type': 'Technical Sell'
        })
        signals['exit_points'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'label': f'SELL: ${sell_price:.2f}',
            'type': 'exit'
        })
    
    # Sell Signal 3: Death Cross (SMA 20 crosses below SMA 50) + Below VWAP
    if sma_20 < sma_50 and (vwap_value is not None and current_price < vwap_value):
        sell_price = current_price
        sell_reason = f"Death Cross (SMA 20 < SMA 50) + Below VWAP"
        signals['sell_signals'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'reason': sell_reason,
            'confidence': 'Medium',
            'type': 'Momentum Sell'
        })
        if not any(abs(e['price'] - sell_price) < 0.01 for e in signals['exit_points']):
            signals['exit_points'].append({
                'price': sell_price,
                'date': hist.index[-1],
                'label': f'SELL: ${sell_price:.2f}',
                'type': 'exit'
            })
    
    # Sell Signal 4: MACD Bearish Crossover + Weak Fundamentals
    if latest_macd < latest_signal and score and score.get('total_score', 100) < 50:
        sell_price = current_price
        sell_reason = f"MACD Bearish + Weak Fundamentals (Score: {score['total_score']}/100)"
        signals['sell_signals'].append({
            'price': sell_price,
            'date': hist.index[-1],
            'reason': sell_reason,
            'confidence': 'Medium',
            'type': 'Momentum Sell'
        })
        if not any(abs(e['price'] - sell_price) < 0.01 for e in signals['exit_points']):
            signals['exit_points'].append({
                'price': sell_price,
                'date': hist.index[-1],
                'label': f'SELL: ${sell_price:.2f}',
                'type': 'exit'
            })
    
    # 3. STOP LOSS and TAKE PROFIT Levels
    
    # Calculate stop loss (5% below lowest buy signal or support)
    if signals['buy_signals']:
        lowest_buy = min(s['price'] for s in signals['buy_signals'])
        stop_loss_price = lowest_buy * 0.95  # 5% stop loss
        if support and support < stop_loss_price:
            stop_loss_price = support * 0.98  # Just below support
        signals['stop_loss'] = {
            'price': stop_loss_price,
            'date': hist.index[-1],
            'reason': f'Stop Loss: 5% below entry or support level'
        }
    
    # Calculate optimal entry suggestion
    optimal_entry = calculate_optimal_entry_price(hist, intrinsic_value, support, vwap, current_price)
    if optimal_entry:
        signals['optimal_entry'] = optimal_entry
    
    # Store resistance level
    if resistance:
        signals['resistance_level'] = {
            'price': resistance,
            'reason': 'Technical Resistance Level',
            'confidence': 'High'
        }
    
    # Calculate take profit targets (if we have buy signals)
    if signals['buy_signals']:
        entry_price = min(s['price'] for s in signals['buy_signals'])
        
        # Take Profit 1: 10% gain
        tp1 = entry_price * 1.10
        signals['take_profit'].append({
            'price': tp1,
            'date': hist.index[-1],
            'label': f'TP1: ${tp1:.2f} (+10%)',
            'target': '10%'
        })
        
        # Take Profit 2: 20% gain
        tp2 = entry_price * 1.20
        signals['take_profit'].append({
            'price': tp2,
            'date': hist.index[-1],
            'label': f'TP2: ${tp2:.2f} (+20%)',
            'target': '20%'
        })
        
        # Take Profit 3: Fair Value (if above entry)
        if intrinsic_value and intrinsic_value > entry_price:
            signals['take_profit'].append({
                'price': intrinsic_value,
                'date': hist.index[-1],
                'label': f'TP3: ${intrinsic_value:.2f} (Fair Value)',
                'target': 'Fair Value'
            })
    
    return signals

def create_trading_signals_chart(data, intrinsic_value=None, metrics=None, score=None):
    """Create professional trading signals chart with buy/sell zones and entry/exit points"""
    if not data:
        return None
    
    hist = data.get('history')
    if hist is None or len(hist) == 0:
        return None
    
    ticker = data.get('ticker', 'Unknown')
    current_price = hist['Close'].iloc[-1] if len(hist) > 0 else 0
    
    # Calculate indicators
    vwap = calculate_vwap(hist)
    support, resistance = calculate_support_resistance(hist)
    
    # Calculate trading signals
    trading_signals = calculate_trading_signals(hist, intrinsic_value, metrics, score, vwap, support, resistance)
    
    if not trading_signals:
        return None
    
    fig = go.Figure()
    
    # Add candlestick chart
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
    
    # Add fair value line if available
    if intrinsic_value and intrinsic_value > 0:
        fair_value_array = np.full(len(hist.index), intrinsic_value)
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=fair_value_array,
            mode='lines',
            name='Fair Value',
            line=dict(color='#667eea', width=2, dash='dash'),
            hovertemplate='Fair Value: $%{y:.2f}<extra></extra>'
        ))
    
    # Add VWAP
    if vwap is not None:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=vwap,
            mode='lines',
            name='VWAP',
            line=dict(color='purple', width=2),
            hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
        ))
    
    # Add support and resistance
    if support:
        fig.add_hline(
            y=support,
            line_dash="dot",
            line_color="green",
            annotation_text=f"Support: ${support:.2f}",
            annotation_position="right",
            opacity=0.7
        )
    if resistance:
        fig.add_hline(
            y=resistance,
            line_dash="dot",
            line_color="red",
            annotation_text=f"Resistance: ${resistance:.2f}",
            annotation_position="right",
            opacity=0.7
        )
    
    # Add instructional BUY signals with educational context
    if trading_signals['buy_signals']:
        for signal in trading_signals['buy_signals']:
            # Create instructional explanation based on signal type
            if signal['type'] == 'Value Buy':
                instruction = f"💡 VALUE BUY<br>${signal['price']:.2f}<br><sub>Undervalued</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Value Buy Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                The stock is trading below its calculated fair value, suggesting it may be undervalued. 
                This is a fundamental analysis signal based on intrinsic value calculations.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider entering a position at ${signal['price']:.2f}<br>
                • Set stop loss below support level<br>
                • Target take profit at fair value or resistance<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>⚠️ Risk reminder:</b> Always use stop losses and never invest more than you can afford to lose.
                """
            elif signal['type'] == 'Technical Buy':
                instruction = f"📊 TECHNICAL BUY<br>${signal['price']:.2f}<br><sub>Oversold + Support</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Technical Buy Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                Technical indicators suggest the stock is oversold (RSI < 30) and price is near a support level. 
                This combination often indicates a potential bounce or reversal.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider entering at ${signal['price']:.2f}<br>
                • Set stop loss just below support<br>
                • Watch for confirmation with volume<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>📖 Learning tip:</b> Technical signals work best when combined with fundamental analysis.
                """
            else:  # Momentum Buy
                instruction = f"🚀 MOMENTUM BUY<br>${signal['price']:.2f}<br><sub>Trending Up</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Momentum Buy Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                Moving averages show a bullish crossover (Golden Cross) and price is above VWAP, 
                indicating strong upward momentum.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider entering at ${signal['price']:.2f}<br>
                • Ride the momentum but watch for reversals<br>
                • Set trailing stop loss<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>📖 Learning tip:</b> Momentum trades can be profitable but require active management.
                """
            
            fig.add_trace(go.Scatter(
                x=[signal['date']],
                y=[signal['price']],
                mode='markers+text',
                name=f"BUY: {signal['type']}",
                marker=dict(
                    size=22,
                    color='#2e7d32',
                    symbol='triangle-up',
                    line=dict(width=2.5, color='white'),
                    opacity=0.9
                ),
                text=[instruction.split('<br>')[0]],  # Main label
                textposition='top center',
                textfont=dict(size=11, color='#2e7d32'),
                hovertemplate=explanation + f"<br><br><b>Entry Price:</b> ${signal['price']:.2f}<extra></extra>",
                showlegend=True
            ))
    
    # Add instructional SELL signals with educational context
    if trading_signals['sell_signals']:
        for signal in trading_signals['sell_signals']:
            # Create instructional explanation based on signal type
            if signal['type'] == 'Value Sell':
                instruction = f"⚠️ VALUE SELL<br>${signal['price']:.2f}<br><sub>Overvalued</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Value Sell Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                The stock is trading above its calculated fair value, suggesting it may be overvalued. 
                This is a fundamental analysis signal indicating potential profit-taking opportunity.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider taking profits at ${signal['price']:.2f}<br>
                • Partial sell: Take some profits, let winners run<br>
                • Full exit: If you've reached your target<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>📖 Learning tip:</b> Selling at fair value helps lock in gains and manage risk.
                """
            elif signal['type'] == 'Technical Sell':
                instruction = f"📊 TECHNICAL SELL<br>${signal['price']:.2f}<br><sub>Overbought + Resistance</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Technical Sell Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                Technical indicators suggest the stock is overbought (RSI > 70) and price is near a resistance level. 
                This combination often indicates a potential pullback or reversal.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider selling at ${signal['price']:.2f}<br>
                • Take profits near resistance<br>
                • Watch for bearish confirmation<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>📖 Learning tip:</b> Resistance levels are where selling pressure typically increases.
                """
            else:  # Momentum Sell
                instruction = f"📉 MOMENTUM SELL<br>${signal['price']:.2f}<br><sub>Trending Down</sub>"
                explanation = f"""
                <b>📚 Educational Guide: Momentum Sell Signal</b><br><br>
                <b>Why this signal?</b><br>
                {signal['reason']}<br><br>
                <b>💡 What this means:</b><br>
                Moving averages show a bearish crossover (Death Cross) and price is below VWAP, 
                indicating downward momentum and potential trend reversal.<br><br>
                <b>✅ Action to consider:</b><br>
                • Consider exiting at ${signal['price']:.2f}<br>
                • Protect capital from further decline<br>
                • Consider shorting if bearish trend confirmed<br>
                • Confidence: {signal['confidence']}<br><br>
                <b>📖 Learning tip:</b> Recognizing trend reversals early helps preserve capital.
                """
            
            fig.add_trace(go.Scatter(
                x=[signal['date']],
                y=[signal['price']],
                mode='markers+text',
                name=f"SELL: {signal['type']}",
                marker=dict(
                    size=22,
                    color='#c62828',
                    symbol='triangle-down',
                    line=dict(width=2.5, color='white'),
                    opacity=0.9
                ),
                text=[instruction.split('<br>')[0]],  # Main label
                textposition='bottom center',
                textfont=dict(size=11, color='#c62828'),
                hovertemplate=explanation + f"<br><br><b>Exit Price:</b> ${signal['price']:.2f}<extra></extra>",
                showlegend=True
            ))
    
    # Add Stop Loss level
    if trading_signals['stop_loss']:
        stop_loss_price = trading_signals['stop_loss']['price']
        fig.add_hline(
            y=stop_loss_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Stop Loss: ${stop_loss_price:.2f}",
            annotation_position="right",
            opacity=0.8,
            line_width=2
        )
    
    
    # Add Take Profit levels
    if trading_signals['take_profit']:
        tp_dates = [tp['date'] for tp in trading_signals['take_profit']]
        tp_prices = [tp['price'] for tp in trading_signals['take_profit']]
        tp_labels = [tp['label'] for tp in trading_signals['take_profit']]
        
        fig.add_trace(go.Scatter(
            x=tp_dates,
            y=tp_prices,
            mode='markers+text',
            name='Take Profit Targets',
            marker=dict(
                size=15,
                color='#ffa726',
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            text=[f"TP<br>${p:.2f}" for p in tp_prices],
            textposition='top center',
            hovertemplate='%{text}<extra></extra>',
            showlegend=True
        ))
        
        # Add horizontal lines for take profit levels
        for tp in trading_signals['take_profit']:
            fig.add_hline(
                y=tp['price'],
                line_dash="dot",
                line_color="orange",
                annotation_text=tp['label'],
                annotation_position="right",
                opacity=0.6
            )
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} Professional Trading Signals - Buy/Sell Zones',
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
        )
    )
    
    return fig, trading_signals

