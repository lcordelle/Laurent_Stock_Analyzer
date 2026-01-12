# 📊 Data Sources - VirtualFusion Stock Analyzer Pro

## Primary Data Source

### **Yahoo Finance** (via `yfinance` Python Library)

The platform uses the **yfinance** library (version 0.2.32) which provides free access to Yahoo Finance data.

**Library:** `yfinance`  
**Website:** https://github.com/ranaroussi/yfinance  
**Data Provider:** Yahoo Finance (finance.yahoo.com)

---

## 📈 Data Retrieved

The platform fetches the following data for each stock analysis:

### 1. **Historical Price Data**
```python
stock.history(period="1y")
```
- **Source:** Yahoo Finance Historical Data
- **Includes:** Open, High, Low, Close, Volume
- **Time Periods Available:** 1mo, 3mo, 6mo, 1y, 2y, 5y, max
- **Update Frequency:** Real-time during market hours (15-minute delay for free tier)

### 2. **Company Information**
```python
stock.info
```
- Company name and description
- Market capitalization
- Current price
- 52-week high/low
- P/E ratios
- Beta
- Analyst ratings
- Dividend information
- And 50+ other metrics

### 3. **Financial Statements**
```python
stock.financials        # Income Statement
stock.balance_sheet     # Balance Sheet
stock.cashflow         # Cash Flow Statement
```
- Quarterly financial data
- Revenue, expenses, profits
- Assets, liabilities, equity
- Operating, investing, financing cash flows

---

## 🔄 Data Flow

```
User Input (Ticker)
        ↓
yfinance.Ticker(ticker)
        ↓
Yahoo Finance API/Website
        ↓
Data Retrieval:
  - Historical prices
  - Company info
  - Financial statements
        ↓
StockAnalyzer Processing
        ↓
Analysis & Scoring
        ↓
Display to User
```

---

## 📍 Where Data is Used

### In `utils/stock_analyzer.py`:

```python
def get_stock_data(self, ticker, period="1y"):
    stock = yf.Ticker(ticker)                    # Connect to Yahoo Finance
    hist = stock.history(period=period)          # Get price history
    info = stock.info                            # Get company info
    financials = stock.financials                 # Get income statement
    balance_sheet = stock.balance_sheet          # Get balance sheet
    cash_flow = stock.cashflow                   # Get cash flow
```

---

## ⚙️ Data Processing

The raw Yahoo Finance data is processed to calculate:

1. **Technical Indicators** (calculated from price history):
   - Moving Averages (SMA 20, 50, 200)
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands

2. **Financial Metrics** (extracted from company info):
   - Valuation ratios (P/E, PEG, Price/Book)
   - Profitability metrics (Margins, ROE, ROA)
   - Growth rates (Revenue Growth, Earnings Growth)
   - Financial health (Debt/Equity, Current Ratio)

3. **Scoring System** (calculated from metrics):
   - Overall score (0-100)
   - Component scores
   - Investment recommendations

---

## 🌐 Network Requirements

- **Internet Connection Required:** Yes
- **API Key Required:** No (free access)
- **Rate Limits:** 
  - Yahoo Finance may throttle excessive requests
  - Recommended: Limit batch operations to 10 stocks max
  - Wait time between requests: Built into yfinance library

---

## ⏰ Data Freshness

| Data Type | Update Frequency | Delay |
|-----------|------------------|-------|
| **Price Data** | Real-time during market hours | ~15 minutes (free tier) |
| **Volume** | Real-time | ~15 minutes |
| **Company Info** | Updated periodically | Varies |
| **Financial Statements** | Quarterly (after earnings) | ~1-2 weeks after quarter end |
| **Analyst Ratings** | Updated regularly | Varies by analyst activity |

---

## 🔒 Data Reliability & Limitations

### ✅ Strengths:
- **Free Access:** No subscription required
- **Comprehensive:** 30+ metrics per stock
- **Reliable Source:** Yahoo Finance is a major financial data provider
- **Real-time During Hours:** Live prices during market hours

### ⚠️ Limitations:
- **Rate Limiting:** Yahoo Finance may throttle excessive requests
- **Data Availability:** Some metrics may be unavailable for smaller companies
- **Exchange Coverage:** Primarily US markets (some international)
- **Free Tier Delays:** 15-minute delay on price data
- **Historical Limits:** Varies by stock (some have limited history)

---

## 🔄 Alternative Data Sources (Future)

The platform architecture allows for easy integration of additional data sources:

### Potential Future Sources:
- **Alpha Vantage API** - Additional financial metrics
- **IEX Cloud** - Real-time and historical data
- **Polygon.io** - Real-time market data
- **Finnhub** - Financial data and news
- **Quandl** - Economic and financial datasets

---

## 📝 Code Location

The data fetching logic is located in:
```
utils/stock_analyzer.py → get_stock_data() method
```

All pages use this method:
- `pages/1_Single_Analysis.py`
- `pages/2_Batch_Comparison.py`
- `pages/3_Stock_Screener.py`
- `pages/4_Reports.py`

---

## 🛠️ Troubleshooting Data Issues

### Issue: "Error fetching data"
**Possible Causes:**
1. Invalid ticker symbol
2. Network connectivity issues
3. Yahoo Finance rate limiting
4. Stock not listed on supported exchange

**Solutions:**
- Verify ticker symbol (e.g., AAPL, not APPL)
- Check internet connection
- Wait a few minutes and retry
- Try a different stock

### Issue: Missing Financial Data
**Possible Causes:**
1. Company is too new (no financial history)
2. Stock listed on unsupported exchange
3. Company doesn't file standard financial statements

**Solutions:**
- Try established stocks with longer history
- Check if stock is listed on major US exchanges
- Some metrics may be unavailable (this is normal)

---

## 📚 Additional Resources

- **yfinance Documentation:** https://github.com/ranaroussi/yfinance
- **Yahoo Finance:** https://finance.yahoo.com
- **Supported Exchanges:** Primarily NYSE, NASDAQ, and other major US exchanges

---

## ⚖️ Legal & Usage

- **Free for Personal Use:** ✅ Yes
- **Commercial Use:** ⚠️ Check Yahoo Finance Terms of Service
- **Data Attribution:** Required (displayed in footer)
- **Disclaimer:** For educational purposes only, not financial advice

---

**Last Updated:** Platform v2.0.0  
**Data Source:** Yahoo Finance via yfinance library








