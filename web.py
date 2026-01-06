# web.py
from flask import Flask
from threading import Thread
import os
from bot import bot  # your bot file

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_bot():
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN missing")
        return
    bot.run(bot_token)

# Start bot in a separate thread
Thread(target=run_bot).start()

# Run Flask in main thread
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
