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
async def lifespan(app: FastAPI):
    print("🚀 Starting Discord bot...")
    bot_task = asyncio.create_task(bot.start(bot_token))
    
    yield  # app runs here
    
    print("🛑 Shutting down bot...")
    await bot.close()
    bot_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def home():
    return {"status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
