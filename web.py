# web.py
from flask import Flask
from threading import Thread
import os
import subprocess
import sys
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_bot():
    """Run the bot in a separate process"""
    print("🤖 Starting Discord bot in background...")
    
    # Method 1: Import and run (if no conflicts)
    try:
        from bot import bot
        bot_token = os.getenv("BOT_TOKEN")
        if bot_token:
            bot.run(bot_token)
    except Exception as e:
        print(f"❌ Couldn't run bot directly: {e}")
        
        # Method 2: Run as subprocess
        print("🔄 Trying subprocess method...")
        subprocess.run([sys.executable, "bot.py"])

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask in main thread (THIS IS WHAT RENDER WANTS)
    print(f"🌐 Starting Flask on port {os.getenv('PORT', 10000)}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
