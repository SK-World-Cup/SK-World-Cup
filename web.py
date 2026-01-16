# web.py - DIRECT IMPORT METHOD
from flask import Flask
import os
import asyncio
import threading
import time

app = Flask(__name__)

# Import and set up bot HERE in main thread
print("🤖 Importing bot module...")
from bot import bot

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("❌ BOT_TOKEN missing")
    exit(1)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_bot_async():
    """Run bot in background"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🤖 Starting bot async...")
        loop.run_until_complete(bot.start(bot_token))
    except Exception as e:
        print(f"❌ Bot failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🌐 Starting Flask on port {os.getenv('PORT', 10000)}")
    
    # Start bot
    bot_thread = threading.Thread(target=run_bot_async, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(5)
    
    # Run Flask
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False, use_reloader=False)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask in main thread
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False, use_reloader=False)
