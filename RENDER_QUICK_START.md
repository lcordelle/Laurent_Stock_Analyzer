# ⚡ Render Quick Start - 5 Minutes

## 🚀 Fastest Way to Deploy

### Step 1: Sign Up (1 minute)
1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (recommended)

### Step 2: Create Web Service (2 minutes)
1. Click **"New +"** → **"Web Service"**
2. Select repository: **`Laurent_Stock_Analyzer`**
3. Click **"Connect"**

### Step 3: Configure (1 minute)
Use these **exact settings**:

**Name**: `stock-analyzer`

**Build Command**:
```
pip install -r requirements.txt
```

**Start Command**:
```
streamlit run main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### Step 4: Deploy (1 minute)
1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build
3. Get your URL: `https://stock-analyzer-xxxx.onrender.com`

**Done! 🎉**

---

## 📱 Access from iPad

1. Open Safari on iPad
2. Go to your Render URL
3. Tap **Share** → **"Add to Home Screen"**
4. Now it's like a native app!

---

## 🔄 Update Your App

Just push to GitHub:
```bash
git add .
git commit -m "Update"
git push
```

Render auto-deploys in 5-10 minutes!

---

## ⚠️ Free Tier Notes

- Sleeps after 15 min inactivity
- First load: 30-60 seconds (waking up)
- 750 hours/month (plenty for personal use)

---

See `RENDER_SETUP_GUIDE.md` for detailed instructions.

