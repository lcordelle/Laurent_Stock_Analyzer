#!/bin/bash

# Script to push Stock Analyzer to GitHub
# Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME

if [ -z "$1" ]; then
    echo "❌ Error: Please provide your GitHub username"
    echo "Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="stock-analyzer"

echo "=========================================="
echo "🚀 Pushing to GitHub"
echo "=========================================="
echo ""
echo "GitHub Username: $GITHUB_USERNAME"
echo "Repository Name: $REPO_NAME"
echo ""

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    echo "⚠️  Remote 'origin' already exists. Updating..."
    git remote set-url origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
else
    echo "➕ Adding GitHub remote..."
    git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
fi

echo ""
echo "📤 Pushing to GitHub..."
echo ""

# Set main branch
git branch -M main

# Push to GitHub
if git push -u origin main; then
    echo ""
    echo "=========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "=========================================="
    echo ""
    echo "📋 Your repository URL:"
    echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "🌐 Next step: Deploy to Render"
    echo "   See DEPLOY_TO_RENDER.md for instructions"
    echo ""
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   1. Repository doesn't exist on GitHub yet"
    echo "   2. Wrong username or repository name"
    echo "   3. Need to authenticate (GitHub may ask for credentials)"
    echo ""
    echo "💡 Make sure you:"
    echo "   - Created the repository on GitHub first"
    echo "   - Used the correct repository name"
    echo "   - Have GitHub authentication set up"
    exit 1
fi

