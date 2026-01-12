# ⏰ Data Timing & Update Frequency

## ❌ NOT Real-Time (Delayed Data)

**Important:** The platform uses **delayed market data**, not real-time data.

---

## ⏱️ Actual Data Delays

### Price & Volume Data
- **Delay:** Approximately **15 minutes** behind live market prices
- **During Market Hours (9:30 AM - 4:00 PM ET):** Data updates every 15-20 minutes
- **After Market Hours:** Shows last closing price
- **Pre-Market/After-Hours:** Limited data availability

### Why the Delay?
- **Free Data Source:** Yahoo Finance provides free data with a delay
- **No Exchange Direct Feed:** Data comes through Yahoo Finance, not direct from exchanges
- **Regulatory:** Free market data typically has mandatory delays for retail users

---

## 📊 Data Update Schedule

| Time Period | Data Status | Delay |
|-------------|-------------|-------|
| **Market Hours** (9:30 AM - 4:00 PM ET) | Updates periodically | ~15 minutes |
| **Pre-Market** (4:00 AM - 9:30 AM ET) | Limited/No data | Varies |
| **After Hours** (4:00 PM - 8:00 PM ET) | Limited data | Varies |
| **Closed Markets** | Last closing price | N/A |
| **Weekends/Holidays** | Last closing price | N/A |

---

## 🔄 What Gets Updated When

### Updated Regularly (During Market Hours)
- ✅ Current stock price (~15 min delay)
- ✅ Trading volume (~15 min delay)
- ✅ Daily high/low prices
- ✅ Bid/ask spreads (if available)

### Updated Periodically (Not Real-Time)
- ⏰ Company information (updates daily/weekly)
- ⏰ Market capitalization (based on delayed price)
- ⏰ P/E ratios and valuation metrics

### Updated Quarterly (Not Real-Time)
- 📅 Financial statements (income statement, balance sheet)
- 📅 Cash flow statements
- 📅 Earnings per share
- 📅 Revenue and profit numbers

### Updated Sporadically
- 📰 Analyst ratings (when analysts update)
- 📰 Target prices (when analysts update)
- 📰 News and company updates

---

## 💡 Example Scenario

**Current Time:** 2:30 PM ET (Market is open)

**What you'll see:**
- Stock price might be from **2:15 PM** (15 min delay)
- Volume data from **2:15 PM**
- All calculations based on the delayed price

**What you WON'T see:**
- Current price at exactly 2:30 PM
- Real-time tick-by-tick updates
- Instant price movements

---

## 🆚 Real-Time vs Delayed Data

### Delayed Data (What This Platform Uses)
- ✅ Free
- ✅ Sufficient for analysis
- ✅ Good for research and planning
- ❌ Not suitable for active day trading
- ❌ 15-minute delay

### True Real-Time Data (Not Available Here)
- 💰 Requires paid subscription ($50-200+/month)
- 💰 Direct exchange feeds
- 💰 Professional trading platforms (Bloomberg, Reuters)
- 💰 Sub-second latency
- 💰 Suitable for active trading

---

## ✅ Suitable For

This delayed data is perfect for:
- ✅ **Investment Research** - Analyzing fundamentals
- ✅ **Long-term Analysis** - Weekly/monthly reviews
- ✅ **Portfolio Planning** - Strategic decisions
- ✅ **Stock Screening** - Finding opportunities
- ✅ **Educational Use** - Learning about stocks

## ❌ NOT Suitable For

Delayed data is NOT suitable for:
- ❌ **Day Trading** - Need real-time prices
- ❌ **Scalping** - Need instant updates
- ❌ **Active Trading** - Need live quotes
- ❌ **Options Trading** - Need real-time volatility

---

## 🔧 How the Platform Handles Data

1. **Each Analysis Refreshes Data**
   - Every time you click "Analyze", it fetches fresh data
   - Data is current as of ~15 minutes ago

2. **No Automatic Refresh**
   - Data doesn't auto-update while viewing
   - Refresh by clicking "Analyze" again

3. **Historical Data**
   - Past prices are accurate (historical data)
   - Only current/latest price has delay

---

## 📈 Bottom Line

**Is the data real-time?** **NO**

**Is the data current enough?** **YES** for most investment research purposes

**The delay:** ~15 minutes behind live market prices

**Best for:** Research, analysis, and strategic planning (not active trading)

---

**Last Updated:** Platform v2.0.0  
**Data Provider:** Yahoo Finance (via yfinance library)  
**Update Frequency:** ~15 minute delay during market hours








