# 📚 GitHub Setup - Step by Step Guide

## 🎯 Goal: Push Your Stock Analyzer App to GitHub

---

## Step 1: Create GitHub Account (if you don't have one)

1. Go to **https://github.com**
2. Click **"Sign up"** (top right)
3. Enter your:
   - Email address
   - Password
   - Username (choose something memorable)
4. Verify your email
5. Complete the setup

**✅ Done?** You now have a GitHub account!

---

## Step 2: Create a New Repository

1. **Log in** to GitHub (https://github.com)
2. Click the **"+"** icon (top right) → **"New repository"**
   - OR go directly to: **https://github.com/new**

3. **Fill in the form:**
   - **Repository name**: `stock-analyzer` (or any name you like)
   - **Description** (optional): "Professional Stock Analyzer with Trading Signals"
   - **Visibility**: 
     - ✅ **Public** (choose this for free Render deployment)
     - ⚠️ Private (requires paid Render plan)
   - **IMPORTANT**: 
     - ❌ **DO NOT** check "Add a README file"
     - ❌ **DO NOT** check "Add .gitignore"
     - ❌ **DO NOT** check "Choose a license"
   - Leave everything else unchecked

4. Click **"Create repository"** (green button at bottom)

**✅ Done?** You now have an empty repository on GitHub!

---

## Step 3: Get Your Repository URL

After creating the repository, GitHub will show you a page with instructions.

**Look for this section:**
```
…or push an existing repository from the command line
```

**You'll see commands like:**
```bash
git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git
git branch -M main
git push -u origin main
```

**📝 Write down your username** - you'll need it!

---

## Step 4: Push Your Code from Terminal

### Option A: Using the Helper Script (Easiest)

1. **Open Terminal** on your Mac
2. **Navigate to your project:**
   ```bash
   cd /Users/laurentcordelle/Downloads/VirtualFusion_Stock_Analyzer
   ```

3. **Run the push script:**
   ```bash
   ./push_to_github.sh YOUR_GITHUB_USERNAME
   ```
   (Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username)

4. **If it asks for authentication:**
   - See Step 5 below

### Option B: Manual Commands

1. **Open Terminal** on your Mac
2. **Navigate to your project:**
   ```bash
   cd /Users/laurentcordelle/Downloads/VirtualFusion_Stock_Analyzer
   ```

3. **Add GitHub as remote:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git
   ```
   (Replace `YOUR_USERNAME` with your actual GitHub username)

4. **Set main branch:**
   ```bash
   git branch -M main
   ```

5. **Push to GitHub:**
   ```bash
   git push -u origin main
   ```

---

## Step 5: Handle Authentication

When you run `git push`, GitHub may ask for authentication.

### Option A: Personal Access Token (Recommended)

1. **Create a token:**
   - Go to: https://github.com/settings/tokens
   - Click **"Generate new token"** → **"Generate new token (classic)"**
   - **Note**: "Stock Analyzer Push"
   - **Expiration**: Choose 90 days or longer
   - **Scopes**: Check **"repo"** (this gives full repository access)
   - Click **"Generate token"**
   - **⚠️ COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

2. **Use the token:**
   - When GitHub asks for **username**: Enter your GitHub username
   - When GitHub asks for **password**: Paste the token (not your actual password)

### Option B: GitHub CLI (Alternative)

1. **Install GitHub CLI:**
   ```bash
   brew install gh
   ```

2. **Authenticate:**
   ```bash
   gh auth login
   ```
   Follow the prompts to authenticate.

### Option C: SSH Keys (Advanced)

If you prefer SSH, you can set up SSH keys. This is more complex but more secure.

---

## Step 6: Verify Success

After pushing, you should see:
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
...
To https://github.com/YOUR_USERNAME/stock-analyzer.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**✅ Success!** Your code is now on GitHub!

---

## Step 7: Check Your Repository

1. Go to: **https://github.com/YOUR_USERNAME/stock-analyzer**
2. You should see all your files!
3. Click on files to view them

**🎉 Congratulations!** Your app is now on GitHub!

---

## 🚀 Next Step: Deploy to Render

Now that your code is on GitHub, you can deploy to Render:

1. Go to **https://render.com**
2. Sign up (free)
3. Click **"New +"** → **"Web Service"**
4. Connect GitHub → Select your `stock-analyzer` repo
5. Deploy!

See `DEPLOY_TO_RENDER.md` for detailed Render instructions.

---

## ❓ Troubleshooting

### Error: "remote origin already exists"
**Solution:**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git
```

### Error: "Authentication failed"
**Solution:**
- Use Personal Access Token (see Step 5)
- Make sure you copied the token correctly
- Token needs "repo" scope

### Error: "Repository not found"
**Solution:**
- Check that you created the repository on GitHub
- Verify the repository name matches
- Make sure repository is Public (or you have access if Private)

### Error: "Permission denied"
**Solution:**
- Check your GitHub username is correct
- Verify you have access to the repository
- Try using Personal Access Token

---

## 📞 Need Help?

- GitHub Docs: https://docs.github.com
- GitHub Support: Available in GitHub dashboard
- Render Docs: https://render.com/docs

---

## ✅ Checklist

- [ ] GitHub account created
- [ ] Repository created on GitHub
- [ ] Repository is Public (for free Render)
- [ ] Code pushed to GitHub
- [ ] Can see files on GitHub website
- [ ] Ready to deploy to Render!

**You're all set! 🎉**

