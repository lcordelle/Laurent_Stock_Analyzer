# 📱 Remote Access Guide - iPhone/iPad Connection

## 🚀 Quick Start (Easiest Method)

### Option 1: LocalTunnel (FREE, No Signup Required) ⭐ RECOMMENDED

1. **Run the setup script:**
   ```bash
   ./start_with_localtunnel.sh
   ```

2. **Wait for the URL to appear** (looks like: `https://xxxxx.loca.lt`)

3. **Open that URL on your iPhone/iPad** - works from anywhere!

**That's it!** No firewall issues, no network configuration needed.

---

### Option 2: ngrok (More Reliable, Free Account Required)

1. **First time setup:**
   ```bash
   ./setup_remote_access.sh
   ```
   
   Or manually:
   - Install: `brew install ngrok/ngrok/ngrok`
   - Sign up at https://dashboard.ngrok.com/signup (free)
   - Get authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
   - Run: `ngrok config add-authtoken YOUR_TOKEN`

2. **Start the app with ngrok (one command):**
   ```bash
   ./start_with_remote.sh
   ```
   
   This starts Streamlit on port 8501 and creates a public ngrok URL.

3. **Use the public URL** (e.g. `https://abc123.ngrok-free.app`) on any device — iPhone, iPad, or computer.

4. **ngrok config:** Uses permanent domain `laurent.ngrok.io` — same URL every time.

---

## 🔧 Troubleshooting

### If LocalTunnel doesn't work:

1. **Check if the app is running:**
   ```bash
   lsof -i:8501
   ```

2. **Try ngrok instead** (more reliable):
   ```bash
   ./start_with_remote.sh
   ```

### If you see connection errors:

- Make sure the Streamlit app is running
- Check the terminal for any error messages
- Try stopping and restarting: Press `Ctrl+C` then run the script again

---

## 📝 What Each Method Does

### LocalTunnel
- ✅ **Free** - No signup required
- ✅ **Easy** - Just run the script
- ✅ **Works from anywhere** - Not limited to same WiFi
- ⚠️ URLs change each time (but that's fine for personal use)

### ngrok
- ✅ **More reliable** - Better uptime
- ✅ **Stable URLs** - Can get fixed URLs with paid plan
- ✅ **Dashboard** - View requests at http://localhost:4040
- ⚠️ Requires free account signup

---

## 🎯 Recommended Workflow

1. **Use LocalTunnel for quick access:**
   ```bash
   ./start_with_localtunnel.sh
   ```

2. **Bookmark the URL on your iPhone/iPad** for easy access

3. **If you need a permanent URL**, use ngrok with a fixed domain

---

## 💡 Pro Tips

- **Add to Home Screen:** Once you have the URL, add it to your iPhone/iPad home screen for one-tap access
- **Keep Terminal Open:** The script needs to keep running to maintain the tunnel
- **Same URL Works Everywhere:** Use the same URL on iPhone, iPad, or any device

---

## 🆘 Still Having Issues?

If neither method works:

1. Check your internet connection
2. Make sure no firewall is blocking Node.js (for LocalTunnel) or ngrok
3. Try restarting your Mac
4. Check the logs:
   - LocalTunnel: `tail -f /tmp/localtunnel.log`
   - ngrok: Check http://localhost:4040


