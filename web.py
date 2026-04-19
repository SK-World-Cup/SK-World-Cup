import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from bot import bot

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise RuntimeError("BOT_TOKEN missing")

# Lifespan handles startup/shutdown cleanly
@asynccontextmanager
async def lifespan(app):
    print("🚀 Starting Discord bot...")

    async def run_bot():
        try:
            await bot.start(bot_token)
        except Exception as e:
            print(f"❌ BOT CRASHED: {e}")

    task = asyncio.create_task(run_bot())

    yield

    print("🛑 Shutting down bot...")
    await bot.close()
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def home():
    return {"status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
