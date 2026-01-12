"""
VirtualFusion Stock Analyzer Pro
Advanced Stock Analysis Platform with AI-Powered Insights
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="VirtualFusion Stock Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #00c853;
    }
    .negative {
        color: #ff1744;
    }
    .neutral {
        color: #ffa726;
    }
</style>
""", unsafe_allow_html=True)

class StockAnalyzer:
    """Advanced Stock Analysis Engine"""
    
    def __init__(self):
        self.cache = {}
    
    def get_stock_data(self, ticker, period="1y"):
        """Fetch comprehensive stock data with caching"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            return {
                'ticker': ticker,
                'history': hist,
                'info': info,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cash_flow': cash_flow,
                'stock_object': stock
            }
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def calculate_score(self, data):
        """Calculate comprehensive stock score (0-100)"""
        if not data:
            return None
        
        info = data['info']
        score = 0
        max_score = 100
        components = {}
        
        # Profitability Score (25 points)
        try:
            gross_margin = info.get('grossMargins', 0) * 100
            if gross_margin > 60:
                score += 25
                components['Gross Margin'] = 25
            elif gross_margin > 40:
                score += 15
                components['Gross Margin'] = 15
            elif gross_margin > 20:
                score += 10
                components['Gross Margin'] = 10
            else:
                components['Gross Margin'] = 5
                score += 5
        except:
            components['Gross Margin'] = 0
        
        # ROE Score (20 points)
        try:
            roe = info.get('returnOnEquity', 0) * 100
            if roe > 20:
                score += 20
                components['ROE'] = 20
            elif roe > 15:
                score += 15
                components['ROE'] = 15
            elif roe > 10:
                score += 10
                components['ROE'] = 10
            else:
                components['ROE'] = 5
                score += 5
        except:
            components['ROE'] = 0
        
        # FCF Margin Score (20 points)
        try:
            fcf_margin = info.get('freeCashflow', 0) / info.get('totalRevenue', 1) * 100
            if fcf_margin > 15:
                score += 20
                components['FCF Margin'] = 20
            elif fcf_margin > 10:
                score += 15
                components['FCF Margin'] = 15
            elif fcf_margin > 5:
                score += 10
                components['FCF Margin'] = 10
            else:
                components['FCF Margin'] = 5
                score += 5
        except:
            components['FCF Margin'] = 0
        
        # Valuation Score (20 points)
        try:
            pe_ratio = info.get('trailingPE', 999)
            if 10 < pe_ratio < 25:
                score += 20
                components['Valuation'] = 20
            elif 5 < pe_ratio < 35:
                score += 15
                components['Valuation'] = 15
            elif pe_ratio < 50:
                score += 10
                components['Valuation'] = 10
            else:
                components['Valuation'] = 5
                score += 5
        except:
            components['Valuation'] = 0
        
        # Growth Score (15 points)
        try:
            revenue_growth = info.get('revenueGrowth', 0) * 100
            if revenue_growth > 20:
                score += 15
                components['Growth'] = 15
            elif revenue_growth > 10:
                score += 10
                components['Growth'] = 10
            elif revenue_growth > 0:
                score += 5
                components['Growth'] = 5
            else:
                components['Growth'] = 0
        except:
            components['Growth'] = 0
        
        return {
            'total_score': min(score, max_score),
            'components': components,
            'max_score': max_score
        }
    
    def get_key_metrics(self, data):
        """Extract key financial metrics"""
        if not data:
            return None
        
        info = data['info']
        hist = data['history']
        
        current_price = hist['Close'].iloc[-1] if len(hist) > 0 else info.get('currentPrice', 0)
        
        metrics = {
            'Current Price': current_price,
            'Today Range': f"${hist['Low'].iloc[-1]:.2f} - ${hist['High'].iloc[-1]:.2f}" if len(hist) > 0 else "N/A",
            '52 Week Range': f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}",
            'Market Cap': info.get('marketCap', 0),
            'P/E Ratio': info.get('trailingPE', 0),
            'Forward P/E': info.get('forwardPE', 0),
            'PEG Ratio': info.get('pegRatio', 0),
            'Price to Book': info.get('priceToBook', 0),
            'Dividend Yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'Volume': hist['Volume'].iloc[-1] if len(hist) > 0 else info.get('volume', 0),
            'Average Volume': info.get('averageVolume', 0),
            'Gross Margin': info.get('grossMargins', 0) * 100,
            'Operating Margin': info.get('operatingMargins', 0) * 100,
            'Profit Margin': info.get('profitMargins', 0) * 100,
            'ROE': info.get('returnOnEquity', 0) * 100,
            'ROA': info.get('returnOnAssets', 0) * 100,
            'Revenue Growth': info.get('revenueGrowth', 0) * 100,
            'Earnings Growth': info.get('earningsGrowth', 0) * 100,
            'Debt to Equity': info.get('debtToEquity', 0),
            'Current Ratio': info.get('currentRatio', 0),
            'Quick Ratio': info.get('quickRatio', 0),
            'Beta': info.get('beta', 0),
            'Target Price': info.get('targetMeanPrice', 0),
            'Analyst Rating': info.get('recommendationKey', 'N/A'),
            'Number of Analysts': info.get('numberOfAnalystOpinions', 0)
        }
        
        return metrics
    
    def calculate_technical_indicators(self, hist):
        """Calculate technical indicators"""
        if hist is None or len(hist) < 50:
            return None
        
        # Moving Averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
        bb_std = hist['Close'].rolling(window=20).std()
        hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
        hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
        
        return hist

def create_price_chart(data):
    """Create interactive price chart with technical indicators"""
    hist = data['history']
    ticker = data['ticker']
    
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='Price'
    ))
    
    # Add moving averages if calculated
    if 'SMA_20' in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], 
                                name='SMA 20', line=dict(color='orange', width=1)))
    if 'SMA_50' in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], 
                                name='SMA 50', line=dict(color='blue', width=1)))
    
    fig.update_layout(
        title=f'{ticker} Price Chart',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        height=500,
        template='plotly_white'
    )
    
    return fig

def create_volume_chart(hist, ticker):
    """Create volume chart"""
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
    """Create comparison table for multiple stocks"""
    comparison_data = []
    
    for ticker, data in stocks_data.items():
        if data is None:
            continue
        
        metrics = analyzer.get_key_metrics(data)
        score = analyzer.calculate_score(data)
        
        comparison_data.append({
            'Ticker': ticker,
            'Company': data['info'].get('longName', ticker),
            'Score': score['total_score'] if score else 0,
            'Price': metrics['Current Price'],
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

def main():
    # Header
    st.markdown('<p class="main-header">📈 VirtualFusion Stock Analyzer Pro</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize analyzer
    analyzer = StockAnalyzer()
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Analysis Options")
        
        analysis_mode = st.radio(
            "Select Mode:",
            ["📊 Single Stock Analysis", "📈 Batch Comparison", "🔍 Stock Screener"]
        )
        
        st.markdown("---")
        st.header("⚙️ Settings")
        
        time_period = st.selectbox(
            "Time Period:",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=3
        )
        
        show_technical = st.checkbox("Show Technical Indicators", value=True)
        show_fundamentals = st.checkbox("Show Fundamental Analysis", value=True)
        
        st.markdown("---")
        st.info("💡 **Tip:** Higher scores indicate better overall financial health")
    
    # Main content area
    if analysis_mode == "📊 Single Stock Analysis":
        st.header("Single Stock Analysis")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="single_ticker").upper()
        with col2:
            analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)
        
        if analyze_btn and ticker:
            with st.spinner(f"Analyzing {ticker}..."):
                data = analyzer.get_stock_data(ticker, period=time_period)
                
                if data:
                    # Calculate metrics and score
                    metrics = analyzer.get_key_metrics(data)
                    score = analyzer.calculate_score(data)
                    
                    # Calculate technical indicators
                    if show_technical:
                        data['history'] = analyzer.calculate_technical_indicators(data['history'])
                    
                    # Display company info
                    st.subheader(f"{data['info'].get('longName', ticker)} ({ticker})")
                    st.write(data['info'].get('longBusinessSummary', 'No description available')[:500] + '...')
                    
                    # Score display
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score_color = 'positive' if score['total_score'] >= 70 else 'negative' if score['total_score'] < 50 else 'neutral'
                        st.markdown(f"### Overall Score")
                        st.markdown(f'<p class="{score_color}" style="font-size: 3rem; font-weight: bold;">{score["total_score"]}/100</p>', 
                                  unsafe_allow_html=True)
                    with col2:
                        st.metric("Current Price", f"${metrics['Current Price']:.2f}")
                    with col3:
                        st.metric("Market Cap", f"${metrics['Market Cap']/1e9:.2f}B" if metrics['Market Cap'] > 1e9 else f"${metrics['Market Cap']/1e6:.2f}M")
                    
                    st.markdown("---")
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 Charts", "📊 Key Metrics", "💰 Financials", "🎯 Technical"])
                    
                    with tab1:
                        # Price chart
                        st.plotly_chart(create_price_chart(data), use_container_width=True)
                        
                        # Volume chart
                        st.plotly_chart(create_volume_chart(data['history'], ticker), use_container_width=True)
                        
                        # Score breakdown
                        st.plotly_chart(create_score_visualization(score), use_container_width=True)
                    
                    with tab2:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("### 📍 Price Information")
                            st.metric("Today's Range", metrics['Today Range'])
                            st.metric("52 Week Range", metrics['52 Week Range'])
                            st.metric("Target Price", f"${metrics['Target Price']:.2f}")
                            st.metric("Beta", f"{metrics['Beta']:.2f}")
                        
                        with col2:
                            st.markdown("### 📊 Valuation")
                            st.metric("P/E Ratio", f"{metrics['P/E Ratio']:.2f}")
                            st.metric("Forward P/E", f"{metrics['Forward P/E']:.2f}")
                            st.metric("PEG Ratio", f"{metrics['PEG Ratio']:.2f}")
                            st.metric("Price/Book", f"{metrics['Price to Book']:.2f}")
                        
                        with col3:
                            st.markdown("### 💵 Returns")
                            st.metric("Dividend Yield", f"{metrics['Dividend Yield']:.2f}%")
                            st.metric("ROE", f"{metrics['ROE']:.2f}%")
                            st.metric("ROA", f"{metrics['ROA']:.2f}%")
                            st.metric("Analyst Rating", metrics['Analyst Rating'].upper())
                    
                    with tab3:
                        st.markdown("### Financial Health Metrics")
                        
                        # Financial metrics chart
                        st.plotly_chart(create_financial_metrics_chart(metrics), use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("### 💰 Profitability")
                            st.metric("Gross Margin", f"{metrics['Gross Margin']:.2f}%")
                            st.metric("Operating Margin", f"{metrics['Operating Margin']:.2f}%")
                            st.metric("Profit Margin", f"{metrics['Profit Margin']:.2f}%")
                        
                        with col2:
                            st.markdown("### 📈 Growth")
                            st.metric("Revenue Growth", f"{metrics['Revenue Growth']:.2f}%")
                            st.metric("Earnings Growth", f"{metrics['Earnings Growth']:.2f}%")
                        
                        with col3:
                            st.markdown("### 🏦 Financial Strength")
                            st.metric("Debt/Equity", f"{metrics['Debt to Equity']:.2f}")
                            st.metric("Current Ratio", f"{metrics['Current Ratio']:.2f}")
                            st.metric("Quick Ratio", f"{metrics['Quick Ratio']:.2f}")
                    
                    with tab4:
                        if show_technical and 'RSI' in data['history'].columns:
                            st.markdown("### Technical Indicators")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # RSI
                                latest_rsi = data['history']['RSI'].iloc[-1]
                                rsi_status = "Oversold" if latest_rsi < 30 else "Overbought" if latest_rsi > 70 else "Neutral"
                                st.metric("RSI (14)", f"{latest_rsi:.2f}", rsi_status)
                                
                                # MACD
                                latest_macd = data['history']['MACD'].iloc[-1]
                                latest_signal = data['history']['Signal'].iloc[-1]
                                macd_trend = "Bullish" if latest_macd > latest_signal else "Bearish"
                                st.metric("MACD", f"{latest_macd:.2f}", macd_trend)
                            
                            with col2:
                                # Moving Average Analysis
                                current_price = data['history']['Close'].iloc[-1]
                                sma_20 = data['history']['SMA_20'].iloc[-1]
                                sma_50 = data['history']['SMA_50'].iloc[-1]
                                
                                ma_trend = "Above" if current_price > sma_20 else "Below"
                                st.metric("Price vs SMA 20", f"${current_price:.2f}", f"{ma_trend} {sma_20:.2f}")
                                
                                ma_trend_50 = "Above" if current_price > sma_50 else "Below"
                                st.metric("Price vs SMA 50", f"${current_price:.2f}", f"{ma_trend_50} {sma_50:.2f}")
                            
                            # RSI Chart
                            fig_rsi = go.Figure()
                            fig_rsi.add_trace(go.Scatter(x=data['history'].index, y=data['history']['RSI'],
                                                        mode='lines', name='RSI'))
                            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                            fig_rsi.update_layout(title='RSI Indicator', height=300, template='plotly_white')
                            st.plotly_chart(fig_rsi, use_container_width=True)
                        else:
                            st.info("Enable 'Show Technical Indicators' in settings to view technical analysis")
    
    elif analysis_mode == "📈 Batch Comparison":
        st.header("Batch Stock Comparison")
        
        st.write("Compare multiple stocks side by side")
        
        # Input for multiple tickers
        tickers_input = st.text_area(
            "Enter stock tickers (comma-separated):",
            value="NVDA, AMD, SOFI, PLTR",
            height=100
        )
        
        compare_btn = st.button("📊 Compare Stocks", type="primary")
        
        if compare_btn and tickers_input:
            tickers = [t.strip().upper() for t in tickers_input.split(',')]
            
            if len(tickers) > 10:
                st.warning("⚠️ Please limit comparison to 10 stocks maximum")
                tickers = tickers[:10]
            
            stocks_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"Fetching data for {ticker}...")
                data = analyzer.get_stock_data(ticker, period=time_period)
                if data:
                    stocks_data[ticker] = data
                progress_bar.progress((i + 1) / len(tickers))
            
            status_text.empty()
            progress_bar.empty()
            
            if stocks_data:
                # Create comparison table
                comparison_df = create_comparison_table(stocks_data, analyzer)
                
                # Display comparison table
                st.subheader("📊 Comparison Results")
                
                # Sort by score
                comparison_df = comparison_df.sort_values('Score', ascending=False)
                
                # Format the dataframe
                st.dataframe(
                    comparison_df.style.background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100)
                                       .format({
                                           'Price': '${:.2f}',
                                           'Market Cap': '${:,.0f}',
                                           'P/E Ratio': '{:.2f}',
                                           'Gross Margin': '{:.2f}%',
                                           'ROE': '{:.2f}%',
                                           'Revenue Growth': '{:.2f}%',
                                           'Debt/Equity': '{:.2f}',
                                           'Dividend Yield': '{:.2f}%'
                                       }),
                    use_container_width=True,
                    height=400
                )
                
                # Score comparison chart
                fig_scores = px.bar(comparison_df, x='Ticker', y='Score', 
                                   title='Overall Score Comparison',
                                   color='Score', color_continuous_scale='RdYlGn')
                fig_scores.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig_scores, use_container_width=True)
                
                # Detailed metrics comparison
                st.subheader("📈 Detailed Metrics Comparison")
                
                # Select metric to compare
                metric_to_compare = st.selectbox(
                    "Select metric to visualize:",
                    ['Gross Margin', 'ROE', 'Revenue Growth', 'P/E Ratio', 'Debt/Equity']
                )
                
                fig_metric = px.bar(comparison_df, x='Ticker', y=metric_to_compare,
                                   title=f'{metric_to_compare} Comparison',
                                   color=metric_to_compare, 
                                   color_continuous_scale='Viridis')
                fig_metric.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig_metric, use_container_width=True)
                
                # Export options
                st.markdown("---")
                st.subheader("💾 Export Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    csv = comparison_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"stock_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    excel_buffer = pd.ExcelWriter('comparison.xlsx', engine='xlsxwriter')
                    comparison_df.to_excel(excel_buffer, index=False, sheet_name='Comparison')
                    excel_buffer.close()
    
    elif analysis_mode == "🔍 Stock Screener":
        st.header("Advanced Stock Screener")
        st.write("Filter stocks based on custom criteria")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("💰 Valuation Filters")
            pe_min = st.number_input("Min P/E Ratio", value=0.0, step=1.0)
            pe_max = st.number_input("Max P/E Ratio", value=100.0, step=1.0)
            
            market_cap_min = st.selectbox(
                "Min Market Cap",
                ["Any", "1M", "10M", "100M", "1B", "10B", "100B"]
            )
        
        with col2:
            st.subheader("📊 Profitability Filters")
            margin_min = st.slider("Min Gross Margin %", 0, 100, 20)
            roe_min = st.slider("Min ROE %", 0, 100, 10)
        
        with col3:
            st.subheader("📈 Growth Filters")
            revenue_growth_min = st.slider("Min Revenue Growth %", -50, 100, 0)
        
        st.markdown("---")
        
        # Stock universe input
        stock_universe = st.text_area(
            "Enter stocks to screen (comma-separated):",
            value="AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, AMD, NFLX, PYPL",
            height=100
        )
        
        screen_btn = st.button("🔍 Run Screener", type="primary")
        
        if screen_btn and stock_universe:
            tickers = [t.strip().upper() for t in stock_universe.split(',')]
            
            passed_stocks = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"Screening {ticker}...")
                data = analyzer.get_stock_data(ticker, period="1y")
                
                if data:
                    metrics = analyzer.get_key_metrics(data)
                    
                    # Apply filters
                    passes = True
                    
                    if metrics['P/E Ratio'] < pe_min or metrics['P/E Ratio'] > pe_max:
                        passes = False
                    
                    if metrics['Gross Margin'] < margin_min:
                        passes = False
                    
                    if metrics['ROE'] < roe_min:
                        passes = False
                    
                    if metrics['Revenue Growth'] < revenue_growth_min:
                        passes = False
                    
                    if passes:
                        passed_stocks.append({
                            'Ticker': ticker,
                            'Company': data['info'].get('longName', ticker),
                            'Price': metrics['Current Price'],
                            'Market Cap': metrics['Market Cap'],
                            'P/E Ratio': metrics['P/E Ratio'],
                            'Gross Margin': metrics['Gross Margin'],
                            'ROE': metrics['ROE'],
                            'Revenue Growth': metrics['Revenue Growth']
                        })
                
                progress_bar.progress((i + 1) / len(tickers))
            
            status_text.empty()
            progress_bar.empty()
            
            if passed_stocks:
                st.success(f"✅ Found {len(passed_stocks)} stocks matching criteria")
                
                results_df = pd.DataFrame(passed_stocks)
                
                st.dataframe(
                    results_df.style.format({
                        'Price': '${:.2f}',
                        'Market Cap': '${:,.0f}',
                        'P/E Ratio': '{:.2f}',
                        'Gross Margin': '{:.2f}%',
                        'ROE': '{:.2f}%',
                        'Revenue Growth': '{:.2f}%'
                    }),
                    use_container_width=True
                )
                
                # Export screener results
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Screener Results",
                    data=csv,
                    file_name=f"screener_results_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No stocks matched the specified criteria")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p><strong>VirtualFusion Stock Analyzer Pro</strong></p>
        <p>Advanced AI-Powered Stock Analysis Platform | Built for Professional Investors</p>
        <p style='font-size: 0.8rem;'>Data provided by Yahoo Finance | For educational purposes only | Not financial advice</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
