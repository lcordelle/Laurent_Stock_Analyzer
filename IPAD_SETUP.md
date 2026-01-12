# 📱 iPad Setup Guide

## Quick Start (2 Steps)

### Step 1: Launch on Your Mac

**Easiest Way:**
- **Double-click** the file `START_FOR_IPAD.command` in Finder
- Or run: `python3 launch_for_ipad.py` in Terminal

### Step 2: Access from iPad

1. **Note the URL** shown in the terminal (e.g., `http://192.168.1.105:8501`)
2. **Open Safari** on your iPad (must be on same Wi-Fi)
3. **Enter that URL** in the address bar
4. **Bookmark it** - Add to Home Screen for app-like experience!

## Adding to iPad Home Screen

1. Open the app in Safari on iPad
2. Tap the **Share button** (square with arrow)
3. Tap **"Add to Home Screen"**
4. Name it "Stock Analyzer" (or whatever you like)
5. Tap **"Add"**

Now it will appear like an app icon on your iPad!

## Requirements

✅ Both devices must be on the **SAME Wi-Fi network**
✅ Your Mac must have **Python 3.8+** installed
✅ Keep the launcher window open while using the app

## Troubleshooting

### "Can't connect" from iPad?

1. **Check Firewall Settings:**
   - System Preferences → Security & Privacy → Firewall
   - Click "Firewall Options"
   - Make sure Python/Terminal is allowed

2. **Verify Same Network:**
   - Mac: System Preferences → Network → Wi-Fi
   - iPad: Settings → Wi-Fi
   - Both should show the same network name

3. **Try Different Port:**
   - If port 8501 is busy, the script will show an error
   - Close other Streamlit apps first

### Finding Your Mac's IP Address

If you need to find it manually:
- System Preferences → Network → Wi-Fi → Advanced → TCP/IP
- Look for "IPv4 Address" (usually starts with 192.168.x.x)

## Using the App

Once connected, you can:
- ✅ Analyze stocks (Single Analysis)
- ✅ Compare multiple stocks (Batch Comparison)  
- ✅ Screen stocks by criteria (Stock Screener)
- ✅ View all charts and metrics
- ✅ Use 12-month forecast projections
- ✅ All features work perfectly on iPad!

The app is fully touch-optimized and works great on iPad screens.

Enjoy! 📊📱








