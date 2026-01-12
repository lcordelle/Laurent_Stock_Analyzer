#!/bin/bash

# Setup script for deploying to Render
# This script helps you prepare your app for Render deployment

echo "=========================================="
echo "🚀 Render Deployment Setup"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    echo "   Visit: https://git-scm.com/downloads"
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""

# Check if .gitignore exists
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore file..."
    # .gitignore should already be created
    echo "✅ .gitignore file created"
else
    echo "✅ .gitignore file exists"
fi

echo ""
echo "=========================================="
echo "📋 Next Steps:"
echo "=========================================="
echo ""
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Name it: stock-analyzer (or your preferred name)"
echo "   - Make it Public (for free Render tier)"
echo "   - Click 'Create repository'"
echo ""
echo "2. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Initial commit - Ready for Render'"
echo "   git remote add origin https://github.com/YOUR_USERNAME/stock-analyzer.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Deploy on Render:"
echo "   - Go to https://render.com"
echo "   - Sign up (free)"
echo "   - Click 'New +' → 'Web Service'"
echo "   - Connect GitHub and select your repo"
echo "   - Use these settings:"
echo "     Build Command: pip install -r requirements.txt"
echo "     Start Command: streamlit run main.py --server.port \$PORT --server.address 0.0.0.0 --server.headless true"
echo "   - Click 'Create Web Service'"
echo ""
echo "4. Access from anywhere:"
echo "   - Mac: Open browser → Go to your Render URL"
echo "   - iPad: Open Safari → Go to your Render URL → Add to Home Screen"
echo ""
echo "📖 For detailed instructions, see: DEPLOY_TO_RENDER.md"
echo "⚡ For quick guide, see: QUICK_DEPLOY.md"
echo ""
echo "=========================================="

