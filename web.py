from flask import Flask
import os
import asyncio

print("🤖 Importing bot module...")
from bot import bot

app = Flask(__name__)

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("❌ BOT_TOKEN missing")
    exit(1)

@app.route("/")
def home():
    return "Discord Bot is running! 🤖"

@app.route("/health")
def health():
    return {"status": "healthy"}

async def main():
    # Start the Discord bot
    bot_task = asyncio.create_task(bot.start(bot_token))

    # Start Flask in a separate thread
    from threading import Thread
    def run_flask():
        print(f"🌐 Starting Flask on port {os.getenv('PORT', 10000)}")
        app.run(
            host="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            debug=False,
            use_reloader=False
        )

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
