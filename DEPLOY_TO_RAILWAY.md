# Quick Railway Deployment Guide

## Files Ready for Deployment:
✓ `bot.py` - Your Discord bot code
✓ `Procfile` - Tells Railway how to run your bot
✓ `railway.json` - Railway configuration
✓ `runtime.txt` - Specifies Python version
✓ `README.md` - Project documentation

## Simple 3-Step Process:

### 1. Create GitHub Repository
- Go to github.com and sign up/login
- Click "New repository" 
- Name: `discord-bot-stats`
- Make it Public
- Create repository

### 2. Upload Files to GitHub
- Download these 5 files from Replit to your computer
- In GitHub, click "uploading an existing file"
- Drag all 5 files into the upload area
- Write message: "Discord bot setup"
- Click "Commit changes"

### 3. Deploy on Railway
- Go to railway.app
- Sign up with GitHub
- Click "New Project" → "Deploy from GitHub repo"
- Select your `discord-bot-stats` repository
- Add environment variables:
  - `BOT_TOKEN` = your Discord token
  - `GOOGLE_CREDS_JSON` = your Google credentials JSON

Your bot will be online 24/7 within 2-3 minutes!

## To Download Files from Replit:
1. Right-click each file in the file explorer
2. Select "Download"
3. Save to a folder on your computer