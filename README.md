# Discord Bot - 1v1 Gaming Stats

A Discord bot that fetches player statistics from Google Sheets and displays them with rich embeds.

## Features
- Fetch player stats with `!playerelo <player_name>`
- Google Sheets integration
- Rich Discord embeds
- Error handling and help commands
- 24/7 uptime capability

## Railway Deployment Instructions

### Step 1: Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and create a new account (if needed)
2. Click "New Repository"
3. Name it something like "discord-bot-stats"
4. Make it Public
5. Click "Create Repository"

### Step 2: Upload Your Code to GitHub
1. Download all files from this Replit project:
   - `bot.py`
   - `Procfile` 
   - `railway.json`
   - `runtime.txt`
   - `README.md`

2. Upload these files to your GitHub repository:
   - Click "uploading an existing file"
   - Drag and drop all the files
   - Write commit message: "Initial bot setup"
   - Click "Commit changes"

### Step 3: Deploy to Railway
1. Go to [Railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your discord-bot-stats repository
6. Railway will automatically detect it's a Python app

### Step 4: Set Environment Variables
In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add these environment variables:
   - `BOT_TOKEN` = (Your Discord bot token)
   - `GOOGLE_CREDS_JSON` = (Your Google credentials JSON)

### Step 5: Deploy
1. Railway will automatically build and deploy
2. Your bot will be online 24/7
3. Check the logs to confirm it's working

## Commands
- `!playerelo <player_name>` - Get player statistics
- `!stats <player_name>` - Same as playerelo
- `!elo <player_name>` - Same as playerelo  
- `!help_stats` - Show help information

## Google Sheets Setup
Your sheet should have columns:
- Player
- Current Elo
- Games
- Record
- K/D Ratio
- Streak