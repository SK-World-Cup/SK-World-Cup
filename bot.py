
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
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)

    sheet = gc.open("1v1 Rankings").sheet1
    match_sheet = gc.open("1v1 Match History").worksheet("1v1 Match History")

    return sheet, match_sheet

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
async def h2h(ctx, *, names):
    try:
        name1, name2 = [n.strip() for n in names.split("vs")]
        data = match_sheet.get_all_values()[1:]  # skip header
        h2h_matches = [row for row in data if (row[0] == name1 and row[2] == name2) or (row[0] == name2 and row[2] == name1)]
        
        if not h2h_matches:
            await ctx.send(f"No match history found between {name1} and {name2}.")
            return

        result_lines = []
        for row in h2h_matches:
            result_lines.append(f"{row[0]} {row[1]} {row[2]}")

        await ctx.send(f"📜 Match history between {name1} and {name2}:\n" + "\n".join(result_lines))

    except Exception as e:
        await ctx.send("❌ Unexpected error occurred.")
        print(f"Error in !h2h command: {e}")


# --- Bot Token ---
bot.run("YOUR_DISCORD_BOT_TOKEN")
