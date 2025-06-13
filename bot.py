
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from threading import Thread

# --- Flask server to keep bot alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_server():
    app.run(host='0.0.0.0', port=5000)

Thread(target=run_server, daemon=True).start()

# --- Google Sheets Setup ---
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)
    rankings_sheet = gc.open("1v1 Rankings").worksheet("Sheet1")
    match_history_sheet = gc.open("1v1 Match History").1v1 Match History
    return rankings_sheet, match_history_sheet

rankings_sheet, match_history_sheet = setup_google_sheets()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- !stats command ---
@bot.command()
async def stats(ctx, *, player_name):
    try:
        values = rankings_sheet.get_all_values()
        headers = values[0]
        data = values[1:]

        for row in data:
            if row[0].strip().lower() == player_name.strip().lower():
                elo = row[2]
                games = row[3]
                record = row[4]
                win_percent = row[5]
                kdr = row[8]
                clean_sheets = row[9]
                streak = row[10]
                await ctx.send(
                    f"📊 Stats for {player_name}\n"
                    f"🔢 Elo: {elo}\n"
                    f"🎮 Games Played: {games}\n"
                    f"📈 Record: {record}\n"
                    f"🏆 Win %: {win_percent}\n"
                    f"⚔️ K/D Ratio: {kdr}\n"
                    f"🧼 Clean Sheets: {clean_sheets}\n"
                    f"🔥 Win Streak: {streak}"
                )
                return
        await ctx.send(f"❌ Player '{player_name}' not found.")
    except Exception as e:
        await ctx.send("⚠️ An error occurred while retrieving stats.")
        print(e)

# --- !h2h command ---
@bot.command()
async def h2h(ctx, *, players):
    try:
        player1, player2 = [p.strip().lower() for p in players.split("vs")]
        all_matches = match_history_sheet.get_all_values()[1:]

        total_matches = 0
        p1_wins = 0
        p2_wins = 0

        for row in all_matches:
            name1 = row[0].strip().lower()
            score = row[1].strip()
            name2 = row[2].strip().lower()

            if (name1 == player1 and name2 == player2) or (name1 == player2 and name2 == player1):
                total_matches += 1
                s1, s2 = map(int, score.split("-"))

                if name1 == player1 and s1 > s2:
                    p1_wins += 1
                elif name2 == player1 and s2 > s1:
                    p1_wins += 1
                else:
                    p2_wins += 1

        if total_matches == 0:
            await ctx.send(f"No head-to-head history between {player1.title()} and {player2.title()}")
        else:
            await ctx.send(
                f"🤜 Head-to-Head: {player1.title()} vs {player2.title()}\n"
                f"📊 Total Matches: {total_matches}\n"
                f"✅ {player1.title()} Wins: {p1_wins}\n"
                f"✅ {player2.title()} Wins: {p2_wins}"
            )
    except Exception as e:
        await ctx.send("⚠️ An error occurred while retrieving match history.")
        print(e)

# --- Bot Token ---
bot.run("YOUR_DISCORD_BOT_TOKEN")
