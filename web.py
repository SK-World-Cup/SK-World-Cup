# web.py
from flask import Flask
import os
import asyncio
import threading
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_bot():
    """Run the bot in its own asyncio event loop"""
    print("🤖 Setting up Discord bot...")
    
    # Create new event loop for the bot thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Import bot inside the thread
        from bot import bot
        
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            print("❌ BOT_TOKEN missing")
            return
        
        print("🤖 Starting Discord bot...")
        loop.run_until_complete(bot.start(bot_token))
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not loop.is_closed():
            loop.close()

if __name__ == "__main__":
    print(f"🌐 Starting Flask on port {os.getenv('PORT', 10000)}")
    
    # Start bot in a daemon thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask in main thread
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False, use_reloader=False)
