
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from threading import Thread

# Flask setup for uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)

Thread(target=run_server, daemon=True).start()

# Google Sheets setup
def setup_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    import json
creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("1v1 Rankings").sheet1
return sheet, client

sheet, gc = setup_google_sheets()

# Discord Bot Setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

@bot.command(name='playerelo')
async def player_elo(ctx, *, player_name: str):
    records = sheet.get_all_records()
    for record in records:
        if record['Player'].lower() == player_name.lower():
            elo = record['Current ELO']
            games = record['Games']
            record_wl = record['Record']
            kdr = record['K/D Ratio']
            streak = record['Streak']
            await ctx.send(
                f"📊 Stats for {player_name}\n"
                f"🔢 Elo: {elo}\n"
                f"🎮 Games Played: {games}\n"
                f"📈 Record: {record_wl}\n"
                f"⚔️ K/D Ratio: {kdr}\n"
                f"🔥 Win Streak: {streak}"
            )
            return
    await ctx.send(f"❌ No player named **{player_name}** found.")

@bot.command(name='h2h')
async def headtohead(ctx, player1: str, player2: str):
    if gc is None:
        await ctx.send("❌ Google Sheets client not initialized.")
        return

    try:
        match_sheet = gc.open("1v1 Rankings").worksheet("1v1 Match History")
        matches = match_sheet.get_all_values()[1:]

        wins_p1, wins_p2 = 0, 0

        for row in matches:
            if len(row) < 3:
                continue
            p1, score, p2 = row[0].strip().lower(), row[1].strip(), row[2].strip().lower()
            player1_lower, player2_lower = player1.lower(), player2.lower()

            if p1 == player1_lower and p2 == player2_lower:
                if score == "1-0":
                    wins_p1 += 1
                elif score == "0-1":
                    wins_p2 += 1
            elif p1 == player2_lower and p2 == player1_lower:
                if score == "1-0":
                    wins_p2 += 1
                elif score == "0-1":
                    wins_p1 += 1

        total_matches = wins_p1 + wins_p2
        if total_matches == 0:
            await ctx.send(f"📉 No head-to-head matches found between {player1} and {player2}.")
        else:
            await ctx.send(
                f"🔁 Head-to-Head Record\n"
                f"{player1}: {wins_p1} wins\n"
                f"{player2}: {wins_p2} wins\n"
                f"🎮 Total Matches: {total_matches}"
            )

    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: {str(e)}")

bot.run("YOUR_DISCORD_BOT_TOKEN")
