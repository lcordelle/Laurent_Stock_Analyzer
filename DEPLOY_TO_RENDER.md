# 🚀 Deploy to Render - Complete Guide

This guide will help you deploy your Stock Analyzer app to Render so you can access it from anywhere on your Mac and iPad.

---

## 📋 Prerequisites

1. **GitHub Account** (free) - https://github.com
2. **Render Account** (free) - https://render.com
3. **Git installed** on your Mac

---

## 🔧 Step 1: Prepare Your Code for GitHub

### 1.1 Initialize Git Repository (if not already done)

```bash
cd /Users/laurentcordelle/Downloads/VirtualFusion_Stock_Analyzer
git init
```

### 1.2 Create .gitignore file

Create a `.gitignore` file to exclude unnecessary files:

```bash
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Streamlit
.streamlit/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data (optional - exclude if you have large data files)
# data/
# *.csv
# *.xlsx

# Logs
*.log
```

### 1.3 Commit Your Code

```bash
git add .
git commit -m "Initial commit - Stock Analyzer app"
```

---

## 📤 Step 2: Push to GitHub

### 2.1 Create a New Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `stock-analyzer` (or any name you prefer)
3. Make it **Public** (free Render tier requires public repos) or **Private** (if you have a paid Render plan)
4. **Don't** initialize with README, .gitignore, or license
5. Click "Create repository"

### 2.2 Push Your Code

GitHub will show you commands. Run these in your terminal:

```bash
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git

# Push your code
git branch -M main
git push -u origin main
```

---

## 🌐 Step 3: Deploy to Render

### 3.1 Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended - easier integration)

### 3.2 Create New Web Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account if not already connected
3. Select your repository: `stock-analyzer`
4. Click **"Connect"**

### 3.3 Configure Your Service

Fill in the settings:

- **Name**: `stock-analyzer` (or any name)
- **Region**: Choose closest to you (e.g., `Oregon (US West)` for US)
- **Branch**: `main`
- **Root Directory**: Leave empty (or `./` if needed)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

### 3.4 Advanced Settings (Optional)

Click **"Advanced"** and add:

- **Environment Variables** (if needed):
  - `PYTHON_VERSION` = `3.11.0`

### 3.5 Deploy

1. Click **"Create Web Service"**
2. Render will start building your app (takes 5-10 minutes)
3. Watch the build logs - it will show progress
4. Once deployed, you'll get a URL like: `https://stock-analyzer-xxxx.onrender.com`

---

## ✅ Step 4: Access from Anywhere

### On Your Mac:

1. Open any web browser (Safari, Chrome, Firefox)
2. Go to your Render URL: `https://stock-analyzer-xxxx.onrender.com`
3. Bookmark it for easy access!

### On Your iPad:

1. Open Safari (or any browser)
2. Go to your Render URL: `https://stock-analyzer-xxxx.onrender.com`
3. Tap the Share button → "Add to Home Screen" to create an app icon
4. Now you can access it like a native app!

---

## 🔧 Troubleshooting

### Issue: App won't start

**Solution**: Check the build logs in Render dashboard. Common issues:
- Missing dependencies in `requirements.txt`
- Wrong start command
- Port configuration issues

### Issue: App is slow to load

**Solution**: 
- Free tier on Render spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds to wake up
- Consider upgrading to paid plan for always-on service

### Issue: Build fails

**Solution**:
- Check that all dependencies are in `requirements.txt`
- Ensure Python version is compatible
- Check build logs for specific error messages

### Issue: Can't access from iPad

**Solution**:
- Make sure you're using the HTTPS URL (not HTTP)
- Check that Render service is running (not sleeping)
- Try refreshing the page

---

## 💰 Render Pricing

### Free Tier:
- ✅ Free forever
- ✅ 750 hours/month (enough for always-on if you use < 25 hours/day)
- ⚠️ Spins down after 15 min inactivity (30-60 sec wake time)
- ✅ Public GitHub repos only

### Paid Tier ($7/month):
- ✅ Always on (no spin-down)
- ✅ Private repos
- ✅ Faster builds
- ✅ Better performance

---

## 🔄 Updating Your App

When you make changes:

1. **Update code locally**
2. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Your update message"
   git push
   ```
3. **Render auto-deploys** - It will automatically detect the push and redeploy (takes 5-10 minutes)

---

## 📱 Pro Tips

1. **Bookmark on iPad**: Add to Home Screen for app-like experience
2. **Custom Domain** (paid): You can use your own domain name
3. **Environment Variables**: Store API keys securely in Render dashboard
4. **Monitoring**: Render dashboard shows logs and metrics
5. **Auto-deploy**: Every GitHub push automatically redeploys

---

## 🎯 Quick Reference

**Your Render URL will be**: `https://YOUR-SERVICE-NAME.onrender.com`

**To update app**: Just push to GitHub, Render auto-deploys!

**To check status**: Go to Render dashboard → Your service → Logs

---

## 📞 Need Help?

- Render Docs: https://render.com/docs
- Render Support: Available in dashboard
- Streamlit on Render: https://docs.streamlit.io/deploy/streamlit-community-cloud

---

## ✅ Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created on Render
- [ ] Build successful
- [ ] App accessible from Mac browser
- [ ] App accessible from iPad browser
- [ ] Bookmarked on both devices

**You're all set! 🎉**

