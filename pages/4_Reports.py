"""
Reports Page
Generate and download professional PDF reports
"""

import streamlit as st
from utils.auth import require_auth
from report_generator import StockReportGenerator
from utils.cache_helpers import get_cached_stock_data
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation
import tempfile
import os

require_auth()

# Page configuration
st.set_page_config(
    page_title="Reports",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Header
render_header("📄 Professional Reports", "Generate and download comprehensive stock analysis reports")

st.markdown("""
Generate professional PDF reports for your stock analysis. Reports include comprehensive metrics, 
score breakdowns, and investment recommendations.
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📊 Single Stock Report
    
    Generate a detailed PDF report for a single stock analysis.
    
    **Includes:**
    - Executive Summary
    - Company Overview
    - Score Breakdown
    - Valuation Metrics
    - Profitability Analysis
    - Growth Metrics
    - Financial Health
    - Investment Recommendation
    """)
    
    ticker = st.text_input("Enter Stock Ticker or Company Name:", value="NVDA", key="report_ticker").strip()
    generate_single = st.button("📄 Generate Single Stock Report", type="primary", use_container_width=True)

with col2:
    st.markdown("""
    ### 📈 Comparison Report
    
    Generate a PDF report comparing multiple stocks.
    
    **Includes:**
    - Comparison Summary
    - Side-by-side Metrics
    - Top Performers
    - Detailed Analysis
    """)
    
    tickers_comparison = st.text_area(
        "Enter tickers or company names (comma-separated):",
        value="NVDA, AMD, INTC",
        height=80,
        key="report_tickers"
    )
    generate_comparison = st.button("📄 Generate Comparison Report", type="primary", use_container_width=True)

if generate_single and ticker:
    with st.spinner(f"Generating report for {ticker}..."):
        try:
            from utils.stock_analyzer import StockAnalyzer
            
            analyzer = StockAnalyzer()
            data = get_cached_stock_data(ticker, "1y")
            
            if data:
                metrics = analyzer.get_key_metrics(data)
                score = analyzer.calculate_score(data)
                resolved_ticker = data.get('ticker', ticker)
                
                generator = StockReportGenerator()
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    output_path = tmp_file.name
                
                generator.generate_single_stock_report(resolved_ticker, data, metrics, score, output_path)
                
                # Read the PDF
                with open(output_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                
                # Provide download
                st.success(f"✅ Report generated for {resolved_ticker}")
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name=f"{resolved_ticker}_analysis_report.pdf",
                    mime="application/pdf"
                )
                
                # Clean up
                os.unlink(output_path)
            else:
                st.error(f"Could not fetch data for {ticker}")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

if generate_comparison and tickers_comparison:
    tickers = [t.strip() for t in tickers_comparison.split(',') if t.strip()]
    
    with st.spinner(f"Generating comparison report for {len(tickers)} stocks..."):
        try:
            from utils.stock_analyzer import StockAnalyzer
            from utils.visualizations import create_comparison_table
            
            analyzer = StockAnalyzer()
            stocks_data = {}
            
            for ticker in tickers:
                data = get_cached_stock_data(ticker, "1y")
                if data:
                    stocks_data[ticker] = data
            
            if stocks_data:
                comparison_df = create_comparison_table(stocks_data, analyzer)
                
                generator = StockReportGenerator()
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    output_path = tmp_file.name
                
                generator.generate_comparison_report(comparison_df, output_path)
                
                # Read the PDF
                with open(output_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                
                # Provide download
                st.success(f"✅ Comparison report generated for {len(stocks_data)} stocks")
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name="stock_comparison_report.pdf",
                    mime="application/pdf"
                )
                
                # Clean up
                os.unlink(output_path)
            else:
                st.error("Could not fetch data for the specified tickers")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

st.markdown("---")

st.info("💡 **Tip:** Reports are generated in real-time using the latest available data. For historical data, use the analysis pages first.")

render_footer()








