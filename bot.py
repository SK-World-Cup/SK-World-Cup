
import os
import discord
from discord.ext import commands, tasks
import gspread
from flask import Flask
import threading

# ——— Configuration ———
RANKINGS_SHEET_ID     = "1YcnHDUZfyngQSVTifaFhSgAlgebf1nQW9ep7FSYwfYY"     # spreadsheet with your “1v1 Rankings” → tab "Sheet1"
MATCH_HISTORY_SHEET_ID= "1LTm-3Am0kVI39bbTpAiA7tzDduB7BRel00AWy0gOhjw"    # spreadsheet with your “1v1 Match History” → tab "1v1 Match History"
REPORT_CHANNEL_ID     = 123456789012345678  # replace with your #match‐reports channel ID

SERVICE_ACCOUNT_FILE  = "creds.json"  # path to your Google service account JSON

POLL_INTERVAL_SECONDS = 60  # how often to check for new matches

# ——— Keep‐alive web server ———
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"
def run_web():
    app.run(host="0.0.0.0", port=8080)
threading.Thread(target=run_web, daemon=True).start()

# ——— Google Sheets setup ———
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
# Rankings sheet & tab
rank_ss   = gc.open_by_key(RANKINGS_SHEET_ID)
rank_ws   = rank_ss.worksheet("Sheet1")
# Match history sheet & tab
match_ss  = gc.open_by_key(MATCH_HISTORY_SHEET_ID)
match_ws  = match_ss.worksheet("1v1 Match History")

# ——— Discord bot setup ———
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Will track how many rows we've already reported
last_reported_row = 0

@bot.event
async def on_ready():
    global last_reported_row
    # Initialize the cursor so we don't repost old entries
    records = match_ws.get_all_records()
    last_reported_row = len(records)
    auto_report_matches.start()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# ——— Command: !playerelo <player> — fetch a player’s Elo from Rankings ———
@bot.command(name="playerelo")
async def playerelo(ctx, *, player: str):
    records = rank_ws.get_all_records()
    for r in records:
        if r["Player"].lower() == player.lower():
            return await ctx.send(f"🎯 **{r['Player']}**’s Elo is **{r['Elo']}**")
    await ctx.send(f"❌ No Elo found for **{player}**.")

# ——— Command: !top10 — list top 10 by Elo ———
@bot.command(name="top10")
async def top10(ctx):
    records = rank_ws.get_all_records()
    top_players = sorted(records, key=lambda x: x["Elo"], reverse=True)[:10]
    embed = discord.Embed(title="🥇 Top 10 Players", color=discord.Color.blue())
    for i, r in enumerate(top_players, start=1):
        embed.add_field(name=f"{i}. {r['Player']}", value=f"Elo: {r['Elo']}", inline=False)
    await ctx.send(embed=embed)

# ——— Command: !help_stats — list available commands ———
@bot.command(name="help_stats")
async def help_stats(ctx):
    help_text = """
**🔹 !playerelo <player>** — Show a player’s current Elo  
**🔹 !top10** — Display the top 10 players by Elo  
**🔹 !help_stats** — Show this help message  
"""
    await ctx.send(help_text)

# ——— Background Task: auto‐report new matches ———
@tasks.loop(seconds=POLL_INTERVAL_SECONDS)
async def auto_report_matches():
    global last_reported_row
    # Fetch all match rows as dicts; assumes header row has keys "Player 1", "Scores", "Player 2"
    records = match_ws.get_all_records()
    current_count = len(records)
    # If there are new rows beyond our cursor...
    if current_count > last_reported_row:
        # Get only the new slice
        new_entries = records[last_reported_row:current_count]
        channel = bot.get_channel(REPORT_CHANNEL_ID)
        for entry in new_entries:
            p1 = entry.get("Player 1") or entry.get("Player1") or entry.get("Player A")
            score = entry.get("Scores") or entry.get("Score") or entry.get("Score A")
            p2 = entry.get("Player 2") or entry.get("Player2") or entry.get("Player B")
            embed = discord.Embed(
                title="📣 New Match Reported",
                description=f"**{p1}** {score} **{p2}**"
            )
            await channel.send(embed=embed)
        # Advance our cursor
        last_reported_row = current_count

# ——— Run the bot ———
if __name__ == "__main__":
    import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
