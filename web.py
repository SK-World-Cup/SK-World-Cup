# web.py
from flask import Flask
import os
import asyncio
import threading
import time

print("🤖 Importing bot module...")
from bot import bot

app = Flask(__name__)

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("❌ BOT_TOKEN missing")
    exit(1)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy"}

def run_bot():
    asyncio.run(bot.start(bot_token))

if __name__ == "__main__":
    print(f"🌐 Starting Flask on port {os.getenv('PORT', 10000)}")

    # Start bot ONCE
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Give bot time to connect
    time.sleep(3)

    # Start Flask ONCE
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        debug=False,
        use_reloader=False
    )

