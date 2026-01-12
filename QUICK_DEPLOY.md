# ⚡ Quick Deploy to Render - 5 Minutes

## 🚀 Fastest Way to Deploy

### Step 1: Push to GitHub (2 minutes)

```bash
cd /Users/laurentcordelle/Downloads/VirtualFusion_Stock_Analyzer

# Initialize git if needed
git init

# Add all files
git add .

# Commit
git commit -m "Deploy to Render"

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render (3 minutes)

1. Go to https://render.com → Sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub → Select your repo
4. Settings:
   - **Name**: `stock-analyzer`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
5. Click **"Create Web Service"**
6. Wait 5-10 minutes for build
7. Get your URL: `https://stock-analyzer-xxxx.onrender.com`

### Step 3: Access from Anywhere

- **Mac**: Open browser → Go to your Render URL
- **iPad**: Open Safari → Go to your Render URL → Add to Home Screen

**Done! 🎉**

---

## 📱 Access from iPad

1. Open Safari on iPad
2. Go to your Render URL
3. Tap Share button (square with arrow)
4. Tap "Add to Home Screen"
5. Now it's like a native app!

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

## ⚠️ Important Notes

- **Free tier**: App sleeps after 15 min inactivity (30-60 sec wake time)
- **First load**: May take 30-60 seconds if app is sleeping
- **Public repo**: Free tier requires public GitHub repo (or upgrade to paid)

---

See `DEPLOY_TO_RENDER.md` for detailed instructions.

