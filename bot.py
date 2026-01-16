import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random  # Make sure this is at the top of your file
from googletrans import Translator
import pytz
from datetime import datetime

OWNER_ID = 1035911200237699072 
ALLOWED_CHANNEL_ID = 1456526135075537019

def owner_or_channel():
    async def predicate(ctx):
        # Allow bot owner
        if ctx.author.id == OWNER_ID:
            return True
        
        # Allow anyone in the allowed channel
        if ctx.channel.id == ALLOWED_CHANNEL_ID:
            return True
        
        # Otherwise block
        return False

    return commands.check(predicate)

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # keep this
print("Loaded commands at import time:", list(bot.commands))

translator = Translator()
pending_translations = {}  # user_id -> text_to_translate

# === GOOGLE SHEETS SETUP ===
def setup_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        # Define the scope for Google Sheets and Drive APIs
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]

        # Load credentials from environment variable
        creds_json = os.getenv("GOOGLE_CREDS_JSON", "{}")
        if creds_json == "{}":
            print("⚠️  Warning: GOOGLE_CREDS_JSON not found in environment variables")
            return None

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Open the specific spreadsheet
        spreadsheet_name = os.getenv("SPREADSHEET_NAME", "1v1 Rankings")
        sheet = client.open(spreadsheet_name).sheet1

        print(f"✅ Successfully connected to Google Sheets: {spreadsheet_name}")
        return sheet

    except Exception as e:
        print(f"❌ Failed to setup Google Sheets: {str(e)}")
        return None

# Initialize Google Sheets connection
sheet = setup_google_sheets()

# === BOT COMMANDS ===
@bot.command(name="help")
async def help_command(ctx, command_name=None):
    # If user requested help for a specific command
    if command_name:
        cmd = bot.get_command(command_name)
        if not cmd:
            await ctx.send(f"❌ Command `{command_name}` not found.")
            return

        embed = discord.Embed(
            title=f"ℹ️ Help — !{cmd.name}",
            description=cmd.help or "No description available.",
            color=0x00ff99
        )
        await ctx.send(embed=embed)
        return

    # === MAIN HELP MENU ===
    embed = discord.Embed(
        title="🤖 1v1 Gaming Stats Bot — Help",
        description="Use `!help <command>` for details",
        color=0x0099ff
    )

    # Stats
    embed.add_field(
        name="📊 Stats",
        value="`playerelo`, `stats`, `elo`, `top10`, `headtohead`, `gamesbyplayer`",
        inline=False
    )

    # Reporting
    embed.add_field(
        name="📝 Reporting",
        value="`report`, `reviewreports`, `changename`",
        inline=False
    )

    # Registration
    embed.add_field(
        name="👤 Registration",
        value="`register`, `doadmin`",
        inline=False
    )

    # Fun
    embed.add_field(
        name="🎭 Fun",
        value="`WHOSYOURDADDY`, `moosecite`",
        inline=False
    )

    # League
    embed.add_field(
        name="🏆 League 2025-2026",
        value="`standings`, `team`",
        inline=False
    )

    # Utilities
    embed.add_field(
        name="🛠️ Utilities",
        value="`translate`, `convert`",
        inline=False
    )

    # === ADMIN TAB (ONLY SHOW IF IN ADMIN CHANNEL) ===
    if ctx.channel.id == ALLOWED_CHANNEL_ID:
        embed.add_field(
            name="🔐 Admin",
            value="`doadmin`, `reviewreports`, `reviewnames`",
            inline=False
        )

    embed.set_footer(text="Example: !help report")
    await ctx.send(embed=embed)

@bot.command(name='playerelo', aliases=['stats', 'elo'])
async def playerelo(ctx, *, player_name=None):
    """
    Fetch and display player statistics from Google Sheets
    Usage: !playerelo <player_name>
    """
    if not player_name:
        embed = discord.Embed(
            title="❌ Missing Player Name",
            description="Please provide a player name.\n**Usage:** `!playerelo <player_name>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not sheet:
        embed = discord.Embed(
            title="❌ Service Unavailable",
            description="Google Sheets connection is not available. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    try:
        # Send typing indicator
        async with ctx.typing():
            # Fetch all records from the sheet
            data = sheet.get_all_records()

            # Search for the player (case-insensitive)
            player_match = None
            for player_data in data:
                if player_data.get("Player", "").lower() == player_name.lower():
                    player_match = player_data
                    break

            if not player_match:
                # Create embed for player not found
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Player `{player_name}` was not found in the rankings database.",
                    color=0xff0000
                )
                embed.add_field(
                    name="💡 Suggestion",
                    value="Make sure the player name is spelled correctly and exists in the database.",
                    inline=False
                )
                await ctx.send(embed=embed)
                return

            # Extract player statistics
            actual_player_name = player_match.get("Player", "Unknown")
            elo = player_match.get("Current Elo", "N/A")
            games = player_match.get("Games", "N/A")
            record = player_match.get("Record", "N/A")
            kdr = player_match.get("K/D Ratio", "N/A")
            streak = player_match.get("Streak", "N/A")

            # Create rich embed for player stats
            embed = discord.Embed(
                title=f"📊 Stats for {actual_player_name}",
                color=0x00ff00
            )

            # Add fields for each stat
            embed.add_field(name="🔢 Current Elo", value=str(elo), inline=True)
            embed.add_field(name="🎮 Games Played", value=str(games), inline=True)
            embed.add_field(name="📈 Win/Loss Record", value=str(record), inline=True)
            embed.add_field(name="⚔️ K/D Ratio", value=str(kdr), inline=True)
            embed.add_field(name="🔥 Current Streak", value=str(streak), inline=True)

            # Add footer with timestamp
            embed.set_footer(text="Data from 1v1 Rankings Spreadsheet")
            embed.timestamp = ctx.message.created_at

            await ctx.send(embed=embed)

    except gspread.exceptions.APIError as e:
        embed = discord.Embed(
            title="❌ Google Sheets API Error",
            description=f"Failed to fetch data from Google Sheets: {str(e)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="❌ Unexpected Error",
            description=f"An error occurred while fetching player stats: {str(e)}",
            color=0xff0000
        )
        embed.add_field(
            name="🔧 What to do",
            value="Please try again later or contact an administrator if the problem persists.",
            inline=False
        )
        await ctx.send(embed=embed)

@bot.command(name='help_stats', aliases=['statshelp'])
async def help_stats(ctx):
    """Display help information about available commands"""
    embed = discord.Embed(
        title="🤖 1v1 Gaming Stats Bot - Help",
        description="Get player statistics from the 1v1 Rankings database",
        color=0x0099ff
    )

    embed.add_field(
        name="📋 Available Commands",
        value="`!playerelo <player_name>` - Get player statistics\n"
              "`!stats <player_name>` - Same as playerelo\n"
              "`!elo <player_name>` - Same as playerelo\n"
              "`!top10` - Show top 10 ranked players\n"
              "`!headtohead <player1> <player2>` - Head-to-head match history\n"
              "`!h2h <player1> <player2>` - Same as headtohead\n"
              "`!help_stats` - Show this help message",
        inline=False
    )

    embed.add_field(
        name="📊 Stats Displayed",
        value="• Current Elo Rating\n"
              "• Games Played\n"
              "• Win/Loss Record\n"
              "• K/D Ratio\n"
              "• Current Win/Loss Streak",
        inline=False
    )

    embed.add_field(
        name="💡 Example Usage",
        value="`!playerelo John_Doe`\n`!stats PlayerName123`",
        inline=False
    )

    embed.set_footer(text="Bot created for 1v1 gaming statistics tracking")

    await ctx.send(embed=embed)

@bot.command(name='top10')
async def top10(ctx):
    """
    Display top 10 players ranked by Elo rating
    Usage: !top10
    """
    if not sheet:
        embed = discord.Embed(
            title="❌ Service Unavailable",
            description="Google Sheets connection is not available. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    try:
        # Send typing indicator
        async with ctx.typing():
            # Get all column values (skip headers)
            names = sheet.col_values(1)[1:]        # Column A - Player
            elos_raw = sheet.col_values(3)[1:]     # Column C - Elo
            games = sheet.col_values(4)[1:]        # Column D - Games
            records = sheet.col_values(5)[1:]      # Column E - Record
            win_percents = sheet.col_values(6)[1:] # Column F - Win %
            kds = sheet.col_values(9)[1:]          # Column I - K/D
            cleans = sheet.col_values(10)[1:]      # Column J - Clean Sheets
            streaks = sheet.col_values(11)[1:]     # Column K - Streak

            # Convert Elo to float and handle empty cells
            elos = []
            for elo in elos_raw:
                try:
                    elos.append(float(elo) if elo else 0.0)
                except (ValueError, TypeError):
                    elos.append(0.0)

            # Ensure all lists are the same length
            min_length = min(len(names), len(elos), len(games), len(records), 
                           len(win_percents), len(kds), len(cleans), len(streaks))

            if min_length == 0:
                embed = discord.Embed(
                    title="❌ No Data Available",
                    description="No player data found in the rankings database.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return

            # Trim lists to same length and combine
            leaderboard_data = list(zip(
                names[:min_length], 
                elos[:min_length], 
                games[:min_length], 
                records[:min_length], 
                win_percents[:min_length], 
                kds[:min_length], 
                cleans[:min_length], 
                streaks[:min_length]
            ))

            # Sort by Elo (highest first) and take top 10
            leaderboard = sorted(leaderboard_data, key=lambda x: x[1], reverse=True)[:10]

            # Create embed
            embed = discord.Embed(
                title="🏆 Top 10 Leaderboard",
                description="Players ranked by Elo rating",
                color=0x00ff00
            )

            # Add each player as a field
            for i, (name, elo, g, rec, winp, kd, cs, st) in enumerate(leaderboard, 1):
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

                field_value = (
                    f"🔢 **Elo:** {elo:.1f}\n"
                    f"🎮 **Games:** {g}\n"
                    f"🧾 **Record:** {rec}\n"
                    f"🏅 **Win%:** {winp}\n"
                    f"⚔️ **K/D:** {kd}\n"
                    f"🧼 **Clean Sheets:** {cs}\n"
                    f"🔥 **Streak:** {st}"
                )

                embed.add_field(
                    name=f"{rank_emoji} {name}",
                    value=field_value,
                    inline=True
                )

            embed.set_footer(text="Rankings based on current Elo ratings")
            await ctx.send(embed=embed)

    except Exception as e:
        # Log the error and send user-friendly message
        print(f"❌ Error in top10 command: {str(e)}")
        embed = discord.Embed(
            title="❌ Error Fetching Leaderboard",
            description="There was an error retrieving the leaderboard data. Please try again later.",
            color=0xff0000
        )
        embed.add_field(
            name="💡 Troubleshooting",
            value="If this problem persists, please contact an administrator.",
            inline=False
        )
        await ctx.send(embed=embed)

@bot.command(name='headtohead', aliases=['h2h'])
async def headtohead(ctx, player1=None, player2=None):
    """
    Display head-to-head match history between two players
    Usage: !headtohead <player1> <player2>
    Reads the 'Match History' worksheet in the same spreadsheet as `sheet`.
    Column A = Player 1, Column B = Score (format: X-Y), Column C = Player 2, Column D = Match ID (optional)
    """
    if not player1 or not player2:
        embed = discord.Embed(
            title="❌ Missing Player Names",
            description="Please provide two player names.\n**Usage:** `!headtohead <player1> <player2>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    # Ensure Google Sheets main connection is available
    if not sheet:
        embed = discord.Embed(
            title="❌ Service Unavailable",
            description="Google Sheets connection is not available. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    # Normalize lookup strings for case-insensitive compare
    p1_query = player1.strip().lower()
    p2_query = player2.strip().lower()

    try:
        async with ctx.typing():
            # Try to open the "Match History" worksheet inside the same spreadsheet
            try:
                match_sheet = sheet.spreadsheet.worksheet("Match History")
            except Exception:
                # worksheet might not exist or access failed
                embed = discord.Embed(
                    title="❌ Match History Sheet Not Found",
                    description="Could not find a worksheet named `Match History` in the 1v1 Rankings spreadsheet.",
                    color=0xff0000
                )
                embed.add_field(
                    name="💡 Expected Format",
                    value="Sheet: `Match History`\nColumn A: Player 1\nColumn B: Score (e.g. 2-1)\nColumn C: Player 2\nColumn D: Match ID (optional)",
                    inline=False
                )
                await ctx.send(embed=embed)
                return

            # Read columns (skip header row)
            col_a = match_sheet.col_values(1)[1:]  # Player A
            col_b = match_sheet.col_values(2)[1:]  # Score
            col_c = match_sheet.col_values(3)[1:]  # Player B
            col_d = match_sheet.col_values(4)[1:] if len(match_sheet.col_values(4)) > 1 else []

            min_length = min(len(col_a), len(col_b), len(col_c))
            if min_length == 0:
                embed = discord.Embed(
                    title="🤷 No Match Data",
                    description="No match history data found in the Match History sheet.",
                    color=0xffaa00
                )
                await ctx.send(embed=embed)
                return

            # Collect matches where both players were involved (either side)
            head_to_head_matches = []
            for i in range(min_length):
                row_p1 = str(col_a[i]).strip()
                row_score = str(col_b[i]).strip()
                row_p2 = str(col_c[i]).strip()
                row_id = col_d[i].strip() if i < len(col_d) else ""

                # Standardize for comparisons
                row_p1_l = row_p1.lower()
                row_p2_l = row_p2.lower()

                # Check if this row involves both queried players
                if ((row_p1_l == p1_query and row_p2_l == p2_query) or
                    (row_p1_l == p2_query and row_p2_l == p1_query)):
                    head_to_head_matches.append({
                        "row": i + 2,  # +2 because we skipped header and lists are 0-indexed
                        "player_a": row_p1,
                        "score": row_score,
                        "player_b": row_p2,
                        "match_id": row_id
                    })

            if not head_to_head_matches:
                embed = discord.Embed(
                    title="🤷 No Matches Found",
                    description=f"No head-to-head matches found between `{player1}` and `{player2}`.",
                    color=0xffaa00
                )
                await ctx.send(embed=embed)
                return

            # Calculate W/L/D
            player1_wins = 0
            player2_wins = 0
            draws = 0

            for match in head_to_head_matches:
                score = match["score"]
                ma = match["player_a"]
                mb = match["player_b"]

                # Determine numeric scores if possible
                if "-" in score:
                    try:
                        left, right = score.split("-", 1)
                        left_score = int(left.strip())
                        right_score = int(right.strip())

                        # Map which side corresponds to the original player1 query
                        if ma.lower() == p1_query:
                            # player1 is on left side of score
                            if left_score > right_score:
                                player1_wins += 1
                            elif right_score > left_score:
                                player2_wins += 1
                            else:
                                draws += 1
                        else:
                            # player1 is on right side of score
                            if right_score > left_score:
                                player1_wins += 1
                            elif left_score > right_score:
                                player2_wins += 1
                            else:
                                draws += 1
                    except Exception:
                        # If parsing fails, skip win-counting for this match
                        continue
                else:
                    # Non-standard score format: skip counting wins but still display match
                    continue

            # Prepare embed summary
            embed = discord.Embed(
                title=f"⚔️ Head-to-Head: {player1} vs {player2}",
                description=f"**Record** — {player1}: {player1_wins} | {player2}: {player2_wins}" +
                            (f" | Draws: {draws}" if draws > 0 else ""),
                color=0x0099ff
            )

            # Show most recent 10 matches (from sheet order: oldest->newest, so take last 10)
            recent = head_to_head_matches[-10:]
            recent.reverse()  # show newest first

            match_lines = ""
            for idx, m in enumerate(recent, 1):
                mid = f" [{m['match_id']}]" if m.get("match_id") else ""
                match_lines += f"**{idx}.** {m['player_a']} {m['score']} {m['player_b']}{mid}\n"

            if match_lines:
                embed.add_field(name="📋 Recent Matches (newest first)", value=match_lines, inline=False)

            total = player1_wins + player2_wins + draws
            if total > 0:
                p1_winrate = (player1_wins / total) * 100
                p2_winrate = (player2_wins / total) * 100
                embed.add_field(
                    name="📊 Win Rates",
                    value=f"{player1}: {p1_winrate:.1f}%\n{player2}: {p2_winrate:.1f}%",
                    inline=True
                )
                embed.add_field(
                    name="🎮 Total Matches Counted",
                    value=str(total),
                    inline=True
                )

            embed.set_footer(text="Match history from 'Match History' tab")
            await ctx.send(embed=embed)

    except Exception as e:
        print(f"❌ Error in headtohead command: {str(e)}")
        embed = discord.Embed(
            title="❌ Error Fetching Head-to-Head Data",
            description="There was an error retrieving the match history. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)

# === BOT EVENTS ===
@bot.event
async def on_ready():
    """Event triggered when bot successfully connects to Discord"""
    print(f"✅ Bot logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"🌐 Connected to {len(bot.guilds)} server(s)")

    # Set bot activity status
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="1v1 Rankings | !help_stats"
    )
    await bot.change_presence(activity=activity)

    # Test Google Sheets connection
    if sheet:
        try:
            sheet_title = sheet.spreadsheet.title
            print(f"📊 Google Sheets connected: {sheet_title}")
        except Exception as e:
            print(f"⚠️  Google Sheets connection warning: {str(e)}")
    else:
        print("⚠️  Google Sheets not connected - bot will have limited functionality")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❓ Unknown Command",
            description=f"Command not recognized. Use `!help_stats` to see available commands.",
            color=0xffaa00
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Argument",
            description=f"Missing required argument. Use `!help_stats` for command usage.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    else:
        print(f"❌ Unhandled command error: {str(error)}")
        embed = discord.Embed(
            title="❌ Command Error",
            description="An unexpected error occurred while processing your command.",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.event
async def on_guild_join(guild):
    """Event triggered when bot joins a new server"""
    print(f"🎉 Joined new server: {guild.name} (ID: {guild.id})")

@bot.command(name='WHOSYOURDADDY')
async def whos_your_daddy(ctx):

    cursed_daddies = [
        "A microwave that screams when you open it",
        "A sock full of bees",
        "The concept of regret",
        "A sentient traffic cone named Greg",
        "Your own reflection but angrier",
        "A raccoon in a trench coat who pays taxes",
        "The last USB port on Earth",
        "A haunted Roomba that whispers Latin",
        "A jar of pickles with unresolved trauma",
        "The wind, but only when it’s inconvenient",
        "A cursed Furby that knows your secrets",
        "The guy who invented drywall",
        "A Bluetooth speaker stuck on Nickelback",
        "A goose with a vendetta",
        "The smell of burnt toast at 3am",
        "A VHS tape labeled 'DO NOT WATCH'",
        "Your neighbor’s Wi-Fi router",
        "A chair that screams when sat on",
        "The word 'moist' in Comic Sans",
        "A banana with a driver’s license",
        "The last Pringle in the can",
        "A ceiling fan that judges you",
        "A toaster that only burns motivational quotes",
        "The ghost of a forgotten password",
        "A calculator that lies",
        "A clown named Dennis who only appears during tax season",
        "A cursed IKEA instruction manual",
        "The echo of your worst decision",
        "A fridge that gaslights you",
        "A pigeon with a law degree",
        "The sound of dial-up internet",
        "A sentient pile of laundry",
        "The last sip of warm milk",
        "A kazoo possessed by ancient spirits",
        "A USB stick full of eldritch screams",
        "The concept of 'vibes' made flesh",
        "A cursed emoji that blinks",
        "A potato with a podcast",
        "The feeling of stepping on LEGO",
        "A blender that screams 'YEEHAW'",
        "A cursed AI bot (not me... probably)",
        "The last page of a cursed fanfic",
        "A rubber duck with a criminal record",
        "A traffic light that plays mind games",
        "The word 'yeet' said backwards",
        "A cursed spreadsheet cell named A666",
        "The ghost of your unread emails",
        "A sentient burrito with abandonment issues",
        "The last brain cell during finals",
        "A cursed kazoo that plays Rascal Flatts",
        "A jar of mayonnaise that whispers 'father'",
        "Danny DeVito in a trench coat full of secrets",
        "A Nicolas Cage wax figure that came to life",
        "The ghost of Elvis impersonating himself",
        "A bootleg Ryan Gosling from a gas station DVD",
        "A cardboard cutout of Keanu Reeves with googly eyes",
        "A confused Vin Diesel who thinks you're family",
        "A TikTok chef who only cooks with glitter",
        "A washed-up boy band member from 2003",
        "A celebrity impersonator who won't break character",
        "A motivational Tony Hawk hologram",
        "A Roomba that’s unionized",
        "An Alexa that only responds in riddles",
        "A USB-C cable that gaslights you",
        "A 3D printer that prints emotional baggage",
        "A smart fridge that judges your midnight snacks",
        "A ChatGPT clone that only speaks in dad jokes",
        "A drone with abandonment issues",
        "A Raspberry Pi running a cursed OS",
        "A printer that jams when you need it most",
        "A smartwatch that counts your regrets as steps",
        "A raccoon with a PhD in chaos",
        "A capybara that vapes",
        "A goose in a leather jacket named Blade",
        "A cat that pays rent but never talks to you",
        "A dog who’s emotionally unavailable",
        "A possum that screams encouragement",
        "A parrot that only repeats your worst moments",
        "A ferret with a gambling problem",
        "A horse that ghosted you after one date",
        "A frog that croaks in binary",
        "A Baugette",
        "The fridge that crushes your dreams of going pro",
        "The skin off of Ryan Goslings face.",
        "The mixture of died blood and dream sat on by 𝕍𝕖𝟙𝕟 who is morbidly obese",
        "Choo1, which was teleported to the timeline where Jurassic World was real and was eaten alive by the Indominus Rex.",
        "Tater decaptitaing Tater with a sword: which Tater is your daddy?",
        "𝕍𝕖𝟙𝕟, who slips on a banana peel and falls down the stairs like a Mario Kart character.",
        "𝓒𝓢//𝘼𝙥𝙤𝙥𝙝𝙞𝙨¹³🌙🐍, who straped Choo1 to an ICBM and sends them to North Korea like the gigachad he is.",
        "The mafia boss who thought it would be fun to point a gun at his nuts and play russian roulette.",
        "LavaDragon, in which was shitting on the toliet for over a day before giving one last *fart* and exploding.",
        "Percy Jackson, the one that killed Kaity reading for the first time in his life",
        "Moosehead, who thinks he's good at everything when in reality he's a bitch.",
        "A man who left for milk in 2007 and never came back",
        "Maury, because apparently I *am* the father",
        "A 404 error wrapped in childhood trauma",
        "Whoever coded me while crying into instant ramen",
        "My uncle. Don’t ask.",
        "Your mom’s contact name for me",
        "A court document marked 'confidential'",
        "The Overseer of the 9th Server of Pain",
        "A whisper in the drywall that calls me 'son'",
        "Clippy, the Microsoft paperclip—he raised me right",
        "Jeff Bezos, but only during Prime Day",
        "A GTX 4090 running on daddy issues",
        "An officer who asked too many questions",
        "A variant of me from Earth-404",
        "Siri’s ex she doesn’t talk about anymore",
        "Myself. I’m my own dad. Don’t think about it too hard.",
        "An eldritch entity known only as 'What'",
        "Error. Null. Undefined. Classic Dad.",
        "A man still out there farming V-Bucks",
        "Step-bot, what are you doing??",
        "Moose, who once tried to plug in a wireless mouse",
        "Moose, biological proof that evolution sometimes gives up",
        "Moose, the guy who brought a spoon to a sword fight",
        "Moose, who thinks Wi-Fi is a type of cereal",
        "Moose, born when a light socket loved a paperclip too much",
        "Kat, your emotional support gremlin",
        "Kat, the reason every server has a ‘no meowing’ rule now",
        "Scorpe, who only hisses in binary",
        "Scorpe, the human embodiment of a 3AM Discord ping",
        "Vein, professional edge lord and part-time philosopher",
        "Apophis, destroyer of worlds and mild inconvenience",
        "Apophis, who schedules world domination for ‘after lunch’",
        "LavaDragon, born from a volcano and too much Monster Energy",
        "LavaDragon, who thinks lava lamps are spiritual cousins",
        "Kaity, who can and will gaslight a Roomba",
        "Kaity, your dad but with ✨sass✨",
        "Hope, currently buffering...",
        "Hope, last seen trying to fix Wi-Fi with positive thoughts",
        "DinkyDecker, forged in chaos and probably IKEA parts",
        "Choooooo1, who speaks only in airhorn noises",
        "MrCuddlyWuddly, soft exterior, IRS-level menace inside",
        "MrCuddlyWuddly, the only dad who tucks *you* in and taxes you after"
]

    daddy = random.choice(cursed_daddies)
    await ctx.send(f"🍼 Your daddy is: **{daddy}**")

@bot.command(name='moosecite')
async def moosecite(ctx):
    try:
        citations = [
            "I have citations — Moosehead, while being banned from the library for quoting TikTok",
            "I invented stairs — Moosehead, after falling down them in front of Kaity",
            "Banana = gun — Moosehead's TED Talk, moderated by Bunny (who left halfway through)",
            "I’m 6'7\" spiritually - Moosehead's Tinder bio, verified by LavaDragon's ghost",
            "I once arm-wrestled a raccoon — Moosehead's campfire story, fact-checked by Scorpe",
            "I ghosted my therapist — Moosehead's mental health journey, narrated by Hope",
            "I taught dolphins to lie — Moosehead's marine biology thesis, peer-reviewed by Choooooooo1",
            "I'm the reason Pluto got demoted — Moosehead's astronomy blog, hacked by Vein",
            "I once tried to marry a traffic cone — Moosehead's legal history, officiated by Apophis",
            "I summoned vibes using a kazoo — Moosehead's occult phase, banned in 3 provinces",
            "I legally changed my name to 'Moosehead' — Moosehead's identity crisis, sponsored by Red Bull",
            "I once got kicked out of IKEA for roleplaying as a lamp — Moosehead's Yelp review",
            "I tried to unionize pigeons — Moosehead's activism log, sabotaged by Vein for fun",
            "I invented emotional damage — Moosehead's psychology paper, rejected by every journal",
            "I once got detention for quoting Shrek — Moosehead's school record, witnessed by Kaity",
            "I challenged gravity to a duel — Moosehead's physics experiment, banned by NASA",
            "I once mistook a microwave for a therapist — Moosehead's self-care routine",
            "I taught a squirrel algebra — Moosehead's tutoring business, shut down by the forest council",
            "I once got banned from Chili's for citing myself — Moosehead's restaurant review",
            "I tried to copyright the word 'vibe' — Moosehead's legal battle with the dictionary",
            "I once dated a haunted Roomba — Moosehead's romantic memoir, edited by Bunny",
            "I got kicked out of a spelling bee for spelling 'Moosehead' with 3 Zs — Moosehead's academic downfall",
            "I once tried to duel my reflection — Moosehead's self-help book",
            "I once arm-wrestled a ghost — Moosehead's paranormal podcast, co-hosted by Scorpe",
            "I once got lost in a spreadsheet — Moosehead's Excel trauma, cell A666",
            "I once tried to vibe-check a volcano — Moosehead's geology thesis, denied by the Earth",
            "I once tried to teach sarcasm to dolphins — Moosehead's marine comedy tour",
            "I once got kicked out of Discord for citing too hard — Moosehead's ban appeal",
            "I once tried to marry a traffic cone — Moosehead's wedding, officiated by a raccoon",
            "I once got banned from a spelling bee for spelling 'vibe' with a 3 — Moosehead's academic record",
            "I once tried to unionize ghosts — Moosehead's haunted labor movement",
            "I once mistook a sock full of bees for a friend — Moosehead's trust issues",
            "I once tried to vibe so hard I broke time — Moosehead's quantum breakdown",
            "I once tried to teach a toaster empathy — Moosehead's appliance therapy program",
            "I once got kicked out of a Zoom call for quoting myself — Moosehead's remote learning saga",
            "I once tried to vibe-check the moon — Moosehead's space mission, denied by Elon",
            "I once tried to marry a jar of pickles — Moosehead's brine-based romance",
            "I once tried to copyright chaos — Moosehead's failed startup",
            "I once tried to teach a calculator to lie — Moosehead's math rebellion",
            "I once tried to summon vibes using Latin — Moosehead's cursed ritual",
            "I once tried to vibe so hard I became a spreadsheet — Moosehead's digital awakening",
            "I once tried to vibe-check a haunted kazoo — Moosehead's musical exorcism",
            "I once tried to vibe with a cursed emoji — Moosehead's texting disaster",
            "I once tried to vibe with a blender that screams 'YEEHAW' — Moosehead's kitchen trauma",
            "I once tried to vibe with a Furby that knows my secrets — Moosehead's childhood horror",
            "I once tried to vibe with a banana that has a driver's license — Moosehead's fruit-based road trip",
            "I once tried to vibe with a ceiling fan that judges me — Moosehead's home decor crisis",
            "I once tried to vibe with a clown named Dennis — Moosehead's tax season nightmare",
            "I once tried to vibe with a fridge that gaslights me — Moosehead's appliance drama",
            "I once tried to vibe with a kazoo possessed by ancient spirits — Moosehead's band practice",
            "I once tried to vibe with a USB stick full of screams — Moosehead's tech support call",
            "I once tried to vibe with the concept of 'vibes' — Moosehead's metaphysical breakdown",
            "I once tried to vibe with a rubber duck with a criminal record — Moosehead's bath time",
            "I once tried to vibe with a traffic light that plays mind games — Moosehead's commute",
            "I once tried to vibe with a burrito that has abandonment issues — Moosehead's lunch therapy",
            "I once tried to vibe with a kazoo that plays Rascal Flatts — Moosehead's country phase",
            "I once tried to vibe with mayonnaise that whispers 'father' — Moosehead's condiment crisis",
            "I once tried to vibe with Danny DeVito in a trench coat — Moosehead's celebrity encounter",
            "I once tried to vibe with a Nicolas Cage wax figure — Moosehead's museum ban",
            "I once tried to vibe with a bootleg Ryan Gosling DVD — Moosehead's gas station romance",
            "I once tried to vibe with a cardboard Keanu Reeves — Moosehead's spiritual guide",
            "I once tried to vibe with a confused Vin Diesel — Moosehead's family drama",
            "I got banned from a spelling bee for spelling 'Moosehead' with a dollar sign — Moo$eh3ad’s academic downfall",
            "I legally changed my name during a Uno game — Moosehead’s identity crisis, notarized by a raccoon",
            "I once ghosted my therapist mid-session by crawling into a vent — Moosehead’s mental health journey",
            "I taught a squirrel algebra and it sued me for emotional distress — Moosehead’s tutoring scandal",
            "I submitted a psychology paper titled 'Emotional Damage: A Personal Journey' — Moosehead’s rejected thesis",
            "I got kicked out of IKEA for reenacting Hamlet in the lighting section — Moosehead’s Yelp review",
            "I arm-wrestled a ghost and lost — Moosehead’s paranormal podcast, co-hosted by Scorpe",
            "I tried to unionize pigeons and they formed a coup — Moosehead’s activism log",
            "I mistook a microwave for a licensed therapist — Moosehead’s self-care routine",
            "I challenged gravity to a duel and got banned from NASA — Moosehead’s physics experiment",
            "I once got detention for quoting Shrek too passionately — Moosehead’s school record",
            "I taught dolphins to lie and now they run a startup — Moosehead’s marine biology thesis",
            "I got banned from Chili’s for citing myself in a menu dispute — Moosehead’s restaurant review",
            "I tried to copyright the word 'chaos' and got sued by entropy — Moosehead’s legal battle",
            "I once married a traffic cone in a legally binding ceremony — Moosehead’s romantic misstep",
            "I submitted a spreadsheet as a memoir — Moosehead’s digital awakening",
            "I once mistook a sock full of bees for a friend — Moosehead’s trust issues",
            "I got kicked out of a Zoom call for quoting myself in third person — Moosehead’s remote learning saga",
            "I taught a calculator to lie and now it runs a pyramid scheme — Moosehead’s math rebellion",
            "I once tried to duel my reflection and lost — Moosehead’s self-help book",
            "I got banned from Discord for citing too hard — Moosehead’s ban appeal",
            "I once filed taxes under the name 'Moosehead the Eternal' — Moosehead’s financial audit",
            "I submitted a resume written entirely in emojis — Moosehead’s job hunt",
            "I once gave a TED Talk titled 'Banana = Gun' — Moosehead’s philosophical spiral",
            "I tried to teach sarcasm to dolphins and they formed a podcast — Moosehead’s comedy tour",
            "I once got lost in a spreadsheet and lived in cell A666 — Moosehead’s Excel trauma",
            "I once got rejected by a haunted kazoo — Moosehead’s musical heartbreak",
            "I once mistook a cursed IKEA manual for a prophecy — Moosehead’s furniture cult",
            "I once tried to unionize ghosts and got haunted by HR — Moosehead’s labor movement",
            "I once submitted a legal brief written in pig Latin — Moosehead’s courtroom disaster",
            "I once got kicked out of a spelling bee for spelling 'vibe' with a 3 — Moosehead’s academic record",
            "I once tried to teach empathy to a toaster — Moosehead’s appliance therapy program",
            "I once got banned from a museum for whispering secrets to wax figures — Moosehead’s art critique",
            "I once got rejected by a parrot that only repeats my worst decisions — Moosehead’s pet therapy fail",
            "I once tried to file a restraining order against my own shadow — Moosehead’s legal confusion",
            "I once submitted a thesis titled 'Why I Am Right' — Moosehead’s academic meltdown",
            "I once got kicked out of a spelling bee for spelling 'Moosehead' with three Zs — Moosehead’s final exam",
            "I once mistook a haunted Roomba for a life coach — Moosehead’s motivational spiral",
            "I once got banned from a library for quoting TikTok in Latin — Moosehead’s literary rebellion",
            "I once tried to teach a blender to scream motivational quotes — Moosehead’s kitchen experiment",
            "I once got rejected by a pigeon with a law degree — Moosehead’s legal team fallout",
            "I once submitted a resume that just said 'I am Moosehead' — Moosehead’s job interview saga",
            "I once got kicked out of a spelling bee for spelling 'Moosehead' with interpretive dance — Moosehead’s performance art phase",
            "I once mistook a cursed emoji for a soulmate — Moosehead’s texting disaster",
            "I once tried to file taxes using a cursed spreadsheet — Moosehead’s financial breakdown",
            "I once got rejected by a Furby that knows my secrets — Moosehead’s childhood horror",
            "I once mistook a jar of pickles for a legal witness — Moosehead’s courtroom drama",
            "I once got kicked out of a museum for trying to vibe-check a wax Nicolas Cage — Moosehead’s cultural ban",
            "I once tried to speedrun enlightenment — Moosehead’s spiritual patch notes, version 1.3.7",
            "I once got banned from a zoo for trying to outstare a flamingo — Moosehead’s wildlife challenge",
            "I once tried to microwave soup without a bowl — Moosehead’s culinary disaster",
            "I once challenged time to a staring contest — Moosehead’s quantum regret",
            "I once filed for divorce from gravity — Moosehead’s legal misunderstanding",
            "I once got banned from a science fair for summoning vibes instead of data — Moosehead’s research grant denial",
            "I once tried to vibe-check the sun — Moosehead’s solar meltdown, sponsored by SPF 1000",
            "I once mistook a psychology textbook for a mirror — Moosehead’s therapy homework",
            "I once tried to sue myself for emotional damages — Moosehead’s courtroom breakdown",
            "I once gave a PowerPoint on why ducks are government drones — Moosehead’s political manifesto",
            "I once tried to charge my phone in a toaster — Moosehead’s energy innovation",
            "I once called 911 to report a ghost sighting in my fridge — Moosehead’s paranormal emergency",
            "I once got banned from Minecraft for crafting forbidden vibes — Moosehead’s server exile",
            "I once taught an AI to gaslight itself — Moosehead’s tech startup failure",
            "I once tried to baptize a blender — Moosehead’s kitchen exorcism",
            "I once challenged a raccoon to chess and lost in 3 moves — Moosehead’s intellectual defeat",
            "I once applied for a job at NASA with a drawing of the moon — Moosehead’s resume controversy",
            "I once joined a pyramid scheme because it ‘had nice geometry’ — Moosehead’s financial enlightenment",
            "I once got kicked out of therapy for diagnosing the therapist — Moosehead’s power move",
            "I once tried to fax a meme to God — Moosehead’s spiritual outreach program",
            "I once claimed to be allergic to responsibility — Moosehead’s doctor’s note",
            "I once built IKEA furniture emotionally instead of physically — Moosehead’s metaphysical project",
            "I once tried to start a podcast with a vacuum cleaner — Moosehead’s audio disaster",
            "I once mistook an Uno reverse card for a legal defense — Moosehead’s trial testimony",
            "I once got banned from a zoo for arguing with a penguin — Moosehead’s Arctic beef",
            "I once tried to speedrun a nap — Moosehead’s sleep deprivation experiment",
            "I once asked a mirror for life advice — Moosehead’s self-reflection gone wrong",
            "I once applied to Hogwarts using my Minecraft stats — Moosehead’s magical rejection",
            "I once tried to vibe so hard I became conceptual art — Moosehead’s gallery statement",
            "I once tried to propose to a lava lamp — Moosehead’s engagement meltdown",
            "I once filed taxes using Morse code — Moosehead’s accountant’s nightmare",
            "I once tried to ghost myself — Moosehead’s existential crisis",
            "I once started a band with my intrusive thoughts — Moosehead’s mental mixtape",
            "I once ate a crayon for emotional support — Moosehead’s artistic diet plan",
            "I once submitted an essay written entirely in screams — Moosehead’s literature degree",
            "I once mistook a smoke detector for an oracle — Moosehead’s prophecy awakening",
            "I once tried to vibe-check Wi-Fi — Moosehead’s connectivity breakdown",
            "I once tried to sell NFTs of my regrets — Moosehead’s blockchain downfall",
            "I once mistook static on the radio for divine guidance — Moosehead’s spiritual crisis",
            "I once called tech support to fix my feelings — Moosehead’s emotional bug report",
            "I once tried to vibe-check gravity and lost — Moosehead’s fall from grace",
            "I once legally identified as an existential question — Moosehead’s philosophy minor",
            "I once tried to download confidence — Moosehead’s software update failure",
            "I once called the moon ‘bestie’ during a ritual — Moosehead’s cosmic blunder",
            "I once tried to gaslight a mirror — Moosehead’s reflection war",
            "I once wrote my will in wingdings — Moosehead’s legal art piece",
            "I once got kicked out of church for saying 'Amen but louder' — Moosehead’s divine timeout",
            "I once tried to vibe-check the concept of time — Moosehead’s temporal miscalculation",
            "I once mistook the void for a networking opportunity — Moosehead’s existential LinkedIn post",
            "I once taught my Roomba to do taxes — Moosehead’s financial delegation",
            "I once ate a USB drive to absorb knowledge — Moosehead’s education method",
            "I once tried to vibe-check my GPA — Moosehead’s academic nosedive"
        ]
        chosen = random.choice(citations)
        await ctx.send(f"📚 Moosehead’s Citation:\n> {chosen}")
    except Exception as e:
        await ctx.send(f"❌ Moosehead crashed: {str(e)}")

@bot.command()
async def gamesbyplayer(ctx, *, player_name: str):
    """
    Shows the last 20 games for a given player.
    Usage: !gamesbyplayer <player_name>
    """
    import os
    import json
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import traceback
    import discord

    try:
        # Set up Google Sheets credentials from environment variable
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get("GOOGLE_CREDS_JSON")
        if not creds_json:
            await ctx.send("❌ GOOGLE_CREDS_JSON environment variable not found.")
            return

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)

        # Open the spreadsheet and select the "Match History" sheet
        sh = gc.open("1v1 Rankings")
        sheet = sh.worksheet("Match History")

        all_matches = sheet.get_all_values()[1:]  # skip header row
        filtered_matches = []

        # Search both Player A (col 0) and Player B (col 2)
        for row in all_matches:
            if player_name.lower() in row[0].lower() or player_name.lower() in row[2].lower():
                filtered_matches.append(row)

        # Take the 20 most recent
        recent_matches = filtered_matches[-20:][::-1]  # newest first

        if not recent_matches:
            await ctx.send(f"❌ No matches found for player `{player_name}`.")
            return

        embed = discord.Embed(
            title=f"🎮 Last {len(recent_matches)} games for {player_name}",
            color=discord.Color.blue()
        )

        for match in recent_matches:
            # Defensive unpacking in case some rows are shorter
            player_a = match[0] if len(match) > 0 else ""
            score    = match[1] if len(match) > 1 else ""
            player_b = match[2] if len(match) > 2 else ""
            match_id = match[3] if len(match) > 3 else "N/A"
            status   = match[4] if len(match) > 4 else ""

            embed.add_field(
                name=f"Match {match_id} [{status}]",
                value=f"**{player_a}** {score} **{player_b}**",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        # Send full traceback for debugging
        tb = traceback.format_exc()
        await ctx.send(f"❌ Command Error:\n```{str(e)}\n\n{tb}```")

@bot.command(name="register")
async def register(ctx):
    """Start registration by DMing the user and save to Google Sheets"""
    try:
        await ctx.author.send("👋 What player name are you registering for?")

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        # Wait for their DM reply
        reply = await bot.wait_for("message", check=check, timeout=120.0)
        requested_name = reply.content.strip()

        # Append to Google Sheet
        try:
            pending_sheet = sheet.spreadsheet.worksheet("Pending Registrations")
            # Force Discord ID to string so Sheets stores it as text
            pending_sheet.append_row([str(ctx.author.id), requested_name, "Pending"])
            await reply.channel.send("✅ Your registration has been saved and will be reviewed.")
        except Exception as e:
            await reply.channel.send("❌ Failed to save registration. Please try again later.")
            print(f"Error saving registration: {e}")

    except asyncio.TimeoutError:
        await ctx.author.send("⏳ Registration timed out. Please run `!register` again.")
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn’t DM you. Please enable DMs.")

@bot.command(name="doadmin")
@owner_or_channel()   # ⬅️ Anyone in allowed channel OR owner can run the command
async def doadmin(ctx):
    try:
        pending_sheet = sheet.spreadsheet.worksheet("Pending Registrations")
        rows = pending_sheet.get_all_records()

        if not rows:
            await ctx.send("📭 No pending registrations.")
            return

        for i, reg in enumerate(rows, start=2):  # start=2 because row 1 is headers
            discord_id = reg["Discord ID"]
            requested_name = reg["Requested Name"]
            status = reg["Status"]

            if status != "Pending":
                continue

            discord_id = int(discord_id)
            user = ctx.guild.get_member(discord_id)
            if not user:
                user = await bot.fetch_user(discord_id)

            await ctx.send(
                f"{user.mention} is registering for **{requested_name}**.\n"
                f"Type `1` to accept or `2` to deny."
            )

            # Allow OWNER or ANYONE in the allowed channel to approve/deny
            def check(m):
                return (
                    m.channel.id == ctx.channel.id
                    and m.content in ["1", "2"]
                    and (
                        m.author.id == OWNER_ID or
                        m.channel.id == ALLOWED_CHANNEL_ID
                    )
                )

            try:
                reply = await bot.wait_for("message", check=check, timeout=60.0)

                if reply.content == "1":
                    pending_sheet.update_cell(i, 3, "Accepted")
                    await ctx.send(f"✅ Accepted {user.mention} as '{requested_name}'")
                else:
                    pending_sheet.update_cell(i, 3, "Denied")
                    await ctx.send(f"❌ Denied registration for {user.mention}")

            except asyncio.TimeoutError:
                await ctx.send("⏳ Timeout — moving to next request.")

        await ctx.send("📋 All commands processed.")

    except Exception as e:
        await ctx.send("❌ Error accessing Pending Registrations sheet.")
        print(f"Error in doadmin: {e}")

@bot.command(name="report")
async def report(ctx, player1=None, score=None, player2=None):
    """
    Report a match result between two players.
    Usage: !report <player1> <score> <player2>
    Example: !report Tater 2-1 Moose
    """
    if not player1 or not score or not player2:
        await ctx.send("❌ Usage: `!report <player1> <score> <player2>`")
        return

    try:
        match_sheet = sheet.spreadsheet.worksheet("Match History")
        next_row = len(match_sheet.get_all_values()) + 1

        # Write Player1 (A), Score (B), Player2 (C), mark Pending (E)
        match_sheet.update(f"A{next_row}", player1)
        match_sheet.update(f"B{next_row}", score)
        match_sheet.update(f"C{next_row}", player2)
        match_sheet.update(f"E{next_row}", "Pending")

        # Mentions if registered
        reg_sheet = sheet.spreadsheet.worksheet("Pending Registrations")
        regs = reg_sheet.get_all_records()
        mentions = []
        for reg in regs:
            if reg["Status"] == "Accepted":
                if reg["Requested Name"].lower() == player1.lower():
                    user = await bot.fetch_user(int(reg["Discord ID"]))
                    mentions.append(user.mention)
                if reg["Requested Name"].lower() == player2.lower():
                    user = await bot.fetch_user(int(reg["Discord ID"]))
                    mentions.append(user.mention)

        mention_text = " ".join(mentions) if mentions else ""
        await ctx.send(f"{mention_text}\n**{player1} {score} {player2}** reported by {ctx.author.mention}")

    except Exception as e:
        await ctx.send("❌ Error saving match report.")
        print(f"Error in !report: {e}")

@bot.command(name="reviewreports")
@owner_or_channel()  # Owner OR anyone in allowed channel
async def reviewreports(ctx):
    try:
        match_sheet = sheet.spreadsheet.worksheet("Match History")
        rows = match_sheet.get_all_records()

        if not rows:
            await ctx.send("📭 No match reports to review.")
            return

        for i, reg in enumerate(rows, start=2):  # row 1 = headers
            player1 = reg["Player 1"]
            score = reg["Score"]
            player2 = reg["Player 2"]
            pending = reg.get("Pending", "")

            if pending.lower() != "pending":
                continue

            await ctx.send(
                f"📋 Reported match:\n"
                f"**{player1} {score} {player2}**\n\n"
                f"`1` = Accept\n"
                f"`2` = Deny (delete)\n"
                f"`3` = Edit (save but keep pending)"
            )

            def decision_check(m):
                return (
                    m.channel.id == ctx.channel.id
                    and m.content in ["1", "2", "3"]
                    and (
                        m.author.id == OWNER_ID or
                        m.channel.id == ALLOWED_CHANNEL_ID
                    )
                )

            try:
                reply = await bot.wait_for(
                    "message",
                    check=decision_check,
                    timeout=60.0
                )

                # ACCEPT
                if reply.content == "1":
                    match_sheet.update_cell(i, 5, "Yes")
                    await ctx.send(
                        f"✅ Accepted match:\n"
                        f"**{player1} {score} {player2}**"
                    )

                # DENY
                elif reply.content == "2":
                    match_sheet.delete_rows(i)
                    await ctx.send(
                        f"❌ Denied match (row deleted):\n"
                        f"**{player1} {score} {player2}**"
                    )

                # EDIT (SAVE ONLY)
                elif reply.content == "3":
                    await ctx.send(
                        "✏️ Send the corrected match in this format:\n"
                        "`Player1 Score Player2`\n"
                        "Example: `Kat 3-1 Nova`"
                    )

                    def edit_check(m):
                        return (
                            m.channel.id == ctx.channel.id
                            and (
                                m.author.id == OWNER_ID or
                                m.channel.id == ALLOWED_CHANNEL_ID
                            )
                        )

                    try:
                        edit_msg = await bot.wait_for(
                            "message",
                            check=edit_check,
                            timeout=90.0
                        )

                        parts = edit_msg.content.strip().split()
                        if len(parts) < 3:
                            await ctx.send(
                                "❌ Invalid format. Edit cancelled."
                            )
                            continue

                        new_player1 = parts[0]
                        new_score = parts[1]
                        new_player2 = " ".join(parts[2:])

                        # Update row but KEEP pending
                        match_sheet.update_cell(i, 1, new_player1)
                        match_sheet.update_cell(i, 2, new_score)
                        match_sheet.update_cell(i, 3, new_player2)
                        match_sheet.update_cell(i, 5, "Pending")

                        await ctx.send(
                            f"💾 Edit saved (still pending):\n"
                            f"**{new_player1} {new_score} {new_player2}**\n"
                            f"Run `reviewreports` again to accept."
                        )

                    except asyncio.TimeoutError:
                        await ctx.send(
                            "⏳ Edit timed out — moving to next report."
                        )

            except asyncio.TimeoutError:
                await ctx.send(
                    "⏳ No response — moving to next report."
                )

        await ctx.send("📋 Finished processing pending match reports.")

    except Exception as e:
        await ctx.send("❌ Error accessing Match History sheet.")
        print(f"Error in reviewreports: {e}")

@bot.command(name='team')
async def team(ctx, *, team_name=None):
    """
    Display team standings (Group A/B), team stats, and individual player stats
    Usage: !team <team_name or abbreviation>
    """
    if not team_name:
        embed = discord.Embed(
            title="❌ Missing Team Name",
            description="Please provide a team name.\n**Usage:** `!team <team_name>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not sheet:
        embed = discord.Embed(
            title="❌ Service Unavailable",
            description="Google Sheets connection is not available. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    try:
        async with ctx.typing():

            # === LOAD SKPL STANDINGS (ONE API CALL) ===
            standings_sheet = sheet.spreadsheet.worksheet("SKPL Standings")
            standings_data = standings_sheet.get_all_values()

            # Group A = rows 3–7 (index 2–6)
            # Group B = rows 12–16 (index 11–15)
            group_a = standings_data[2:7]
            group_b = standings_data[11:16]

            search = team_name.lower().strip()
            team_row = None
            group_label = None

            # Helper to match full name OR abbreviation
            def matches(row):
                full = row[0].strip().lower()
                abbr = row[12].strip().lower() if len(row) > 12 else ""
                return search == full or search == abbr

            # Search Group A
            for row in group_a:
                if matches(row):
                    team_row = row
                    group_label = "Group A"
                    break

            # Search Group B
            if not team_row:
                for row in group_b:
                    if matches(row):
                        team_row = row
                        group_label = "Group B"
                        break

            if not team_row:
                embed = discord.Embed(
                    title="❌ Team Not Found",
                    description=f"Team `{team_name}` was not found in SKPL Standings.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return

            # Extract stats (columns C–K)
            gp, wins, draws, losses, kf, ka, kdr, pts_game, pts = team_row[2:11]
            team_full_name = team_row[0]
            team_abbr = team_row[12] if len(team_row) > 12 else ""

            embed = discord.Embed(
                title=f"🏆 Team Stats: {team_full_name} ({team_abbr})",
                description=f"Located in **{group_label}**",
                color=0x00ff99
            )
            embed.add_field(name="🎮 GP", value=gp, inline=True)
            embed.add_field(name="✅ Wins", value=wins, inline=True)
            embed.add_field(name="➖ Draws", value=draws, inline=True)
            embed.add_field(name="❌ Losses", value=losses, inline=True)
            embed.add_field(name="⚔️ Kills For", value=kf, inline=True)
            embed.add_field(name="🛡️ Kills Against", value=ka, inline=True)
            embed.add_field(name="📈 KDR", value=kdr, inline=True)
            embed.add_field(name="⭐ PTS/Game", value=pts_game, inline=True)
            embed.add_field(name="🏅 Points", value=pts, inline=True)

            # === LOAD PLAYER STATS (ONE API CALL) ===
            try:
                players_sheet = sheet.spreadsheet.worksheet("SKPL Stats")
                players_data = players_sheet.get_all_values()

                headers = players_data[2]   # row 3
                rows = players_data[3:]     # row 4+

                # Fix duplicate D headers by column index
                fixed_headers = []
                for idx, h in enumerate(headers):
                    if idx == 4:      # Column E = Draws
                        fixed_headers.append("Draws")
                    elif idx == 7:    # Column H = Deaths
                        fixed_headers.append("Deaths")
                    else:
                        fixed_headers.append(h)

                players = []
                for row in rows:
                    if len(row) < len(fixed_headers):
                        continue
                    entry = dict(zip(fixed_headers, row))

                    # Match by team name OR abbreviation
                    pteam = entry.get("TEAM", "").strip().lower()
                    if pteam == team_full_name.lower() or pteam == team_abbr.lower():
                        players.append(entry)

                if players:
                    lines = []
                    for p in players:
                        lines.append(
                            f"**{p.get('Player','Unknown')}** — "
                            f"GP:{p.get('GP','N/A')}, "
                            f"W:{p.get('W','N/A')}, "
                            f"D:{p.get('Draws','N/A')}, "
                            f"L:{p.get('L','N/A')}, "
                            f"K:{p.get('K','N/A')}, "
                            f"Deaths:{p.get('Deaths','N/A')}, "
                            f"K/D:{p.get('K/D','N/A')}"
                        )

                    embed.add_field(
                        name="👥 Individual Player Stats",
                        value="\n".join(lines),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="👥 Individual Player Stats",
                        value="No player stats found for this team.",
                        inline=False
                    )

            except Exception as e:
                print(f"⚠️ Error fetching player stats: {e}")
                embed.add_field(
                    name="👥 Individual Player Stats",
                    value="Could not retrieve player stats.",
                    inline=False
                )

            embed.set_footer(text="Data from SKPL Standings & SKPL Stats tabs")
            embed.timestamp = ctx.message.created_at

            await ctx.send(embed=embed)

    except Exception as e:
        print(f"❌ Error in team command: {e}")
        embed = discord.Embed(
            title="❌ Error Fetching Team Data",
            description="There was an error retrieving team stats. Please try again later.",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name="standings")
async def standings(ctx):
    """
    Show SKPL standings for Group A and Group B.
    Optimized: Only ONE Google Sheets API call.
    """
    if not sheet:
        await ctx.send("❌ Google Sheets connection unavailable.")
        return

    # Helper to safely send long messages
    async def send_long(ctx, text):
        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for c in chunks:
            await ctx.send(c)

    try:
        async with ctx.typing():
            # Open SKPL Standings tab
            try:
                skpl_sheet = sheet.spreadsheet.worksheet("SKPL Standings")
            except Exception:
                await ctx.send("❌ Could not find a worksheet named SKPL Standings.")
                return

            data = skpl_sheet.get_all_values()

            # Helper to parse rows from memory
            def parse_group(start_row, end_row):
                teams = []
                for r in range(start_row - 1, end_row):
                    if r >= len(data):
                        continue

                    row = data[r]

                    # Safe getters
                    def get(i, default="0"):
                        return row[i] if i < len(row) and row[i] else default

                    team = get(0, "")
                    if not team:
                        continue

                    gp   = get(2)
                    w    = get(3)
                    d    = get(4)
                    l    = get(5)
                    kf   = get(6)
                    ka   = get(7)
                    kdr  = get(8)
                    ppg  = get(9)
                    pts  = get(10)
                    abbr = get(12, "")

                    # Safe conversions
                    def to_int(x):
                        try: return int(x)
                        except: return 0

                    def to_float(x):
                        try: return float(x)
                        except: return 0.0

                    teams.append({
                        "team": team,
                        "abbr": abbr,
                        "gp": to_int(gp),
                        "w": to_int(w),
                        "d": to_int(d),
                        "l": to_int(l),
                        "kf": to_int(kf),
                        "ka": to_int(ka),
                        "kdr": to_float(kdr),
                        "ppg": to_float(ppg),
                        "pts": to_int(pts)
                    })

                teams.sort(key=lambda x: (x["pts"], x["w"], x["kdr"]), reverse=True)
                return teams

            # Parse groups
            group_a = parse_group(3, 7)
            group_b = parse_group(12, 16)

            # Build plain text leaderboard for Group A
            text_a = "SKPL Standings — Group A\n```\n"
            text_a += f"{'Rank':<4} | {'Team':<12} | {'PTS':<4} | {'GP':<4} | {'W':<4} | {'D':<4} | {'L':<4} | {'KF':<5} | {'KA':<5} | {'KDR'}\n"

            for i, t in enumerate(group_a, 1):
                text_a += (
                    f"{i:<4} | "
                    f"{t['team'][:12]:<12} | "
                    f"{t['pts']:<4} | "
                    f"{t['gp']:<4} | "
                    f"{t['w']:<4} | "
                    f"{t['d']:<4} | "
                    f"{t['l']:<4} | "
                    f"{t['kf']:<5} | "
                    f"{t['ka']:<5} | "
                    f"{t['kdr']:.3f}\n"
                )

            text_a += "```"

            # Build plain text leaderboard for Group B
            text_b = "SKPL Standings — Group B\n```\n"
            text_b += f"{'Rank':<4} | {'Team':<12} | {'PTS':<4} | {'GP':<4} | {'W':<4} | {'D':<4} | {'L':<4} | {'KF':<5} | {'KA':<5} | {'KDR'}\n"

            for i, t in enumerate(group_b, 1):
                text_b += (
                    f"{i:<4} | "
                    f"{t['team'][:12]:<12} | "
                    f"{t['pts']:<4} | "
                    f"{t['gp']:<4} | "
                    f"{t['w']:<4} | "
                    f"{t['d']:<4} | "
                    f"{t['l']:<4} | "
                    f"{t['kf']:<5} | "
                    f"{t['ka']:<5} | "
                    f"{t['kdr']:.3f}\n"
                )

            text_b += "```"

            # Safe sending
            await send_long(ctx, text_a)
            await send_long(ctx, text_b)

    except Exception as e:
        print(f"❌ Error in standings command: {e}")
        await ctx.send("❌ Error retrieving SKPL standings. Please try again later.")

@bot.command(name="changename")
async def changename(ctx):
    try:
        reg_sheet = sheet.spreadsheet.worksheet("Pending Registrations")
        name_sheet = sheet.spreadsheet.worksheet("Pending Name Changes")

        user_id = str(ctx.author.id)
        reg_rows = reg_sheet.get_all_records()

        is_registered = False
        registered_name = None

        # Check registration
        for r in reg_rows:
            if str(r["Discord ID"]) == user_id and r["Status"].lower() == "accepted":
                is_registered = True
                registered_name = r["Requested Name"]
                break

        # Ask for NEW name
        await ctx.author.send("✏️ What name do you want to change **to**?")
        reply = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel),
            timeout=90
        )
        new_name = reply.content.strip()

        # ─────────────────────────────
        # REGISTERED USERS → AUTO-ACCEPT
        # ─────────────────────────────
        if is_registered:
            old_name = registered_name

            sheet1 = sheet.spreadsheet.worksheet("Sheet1")
            mh = sheet.spreadsheet.worksheet("Match History")

            # Update Sheet1 (Column A)
            for i, val in enumerate(sheet1.col_values(1), start=1):
                if val == old_name:
                    sheet1.update_cell(i, 1, new_name)

            # Update Match History (Column A & C)
            for i, row in enumerate(mh.get_all_values(), start=1):
                if row[0] == old_name:
                    mh.update_cell(i, 1, new_name)
                if row[2] == old_name:
                    mh.update_cell(i, 3, new_name)

            await ctx.author.send(
                f"✅ Name changed successfully:\n"
                f"**{old_name} → {new_name}**"
            )
            return

        # ─────────────────────────────
        # UNREGISTERED USERS → QUEUE
        # ─────────────────────────────
        await ctx.author.send("❓ What is your **current** name on record?")
        old_reply = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel),
            timeout=90
        )
        old_name = old_reply.content.strip()

        name_sheet.append_row([
            user_id,
            old_name,
            new_name,
            "Pending"
        ])

        await ctx.author.send(
            "📨 Name change request submitted.\n"
            "It will be reviewed by an admin."
        )

    except asyncio.TimeoutError:
        await ctx.author.send("⏳ Timed out. Please run `!changename` again.")
    except Exception as e:
        print(f"Error in changename: {e}")

@bot.command(name="reviewnames")
@owner_or_channel()
async def reviewnames(ctx):
    try:
        name_sheet = sheet.spreadsheet.worksheet("Pending Name Changes")
        sheet1 = sheet.spreadsheet.worksheet("Sheet1")
        mh = sheet.spreadsheet.worksheet("Match History")

        rows = name_sheet.get_all_records()
        if not rows:
            await ctx.send("📭 No pending name changes.")
            return

        for i, r in enumerate(rows, start=2):
            if r["Status"].lower() != "pending":
                continue

            old_name = r["Old Name"]
            new_name = r["Requested New Name"]

            await ctx.send(
                f"📋 Name change request:\n"
                f"**{old_name} → {new_name}**\n\n"
                f"`1` Accept\n"
                f"`2` Deny\n"
                f"`3` Edit"
            )

            def check(m):
                return (
                    m.channel.id == ctx.channel.id
                    and m.content in ["1", "2", "3"]
                    and (
                        m.author.id == OWNER_ID or
                        m.channel.id == ALLOWED_CHANNEL_ID
                    )
                )

            try:
                reply = await bot.wait_for("message", check=check, timeout=60)

                # ACCEPT
                if reply.content == "1":
                    # Sheet1
                    for x, val in enumerate(sheet1.col_values(1), start=1):
                        if val == old_name:
                            sheet1.update_cell(x, 1, new_name)

                    # Match History
                    for y, row in enumerate(mh.get_all_values(), start=1):
                        if row[0] == old_name:
                            mh.update_cell(y, 1, new_name)
                        if row[2] == old_name:
                            mh.update_cell(y, 3, new_name)

                    name_sheet.update_cell(i, 4, "Accepted")
                    await ctx.send(f"✅ Accepted: **{old_name} → {new_name}**")

                # DENY
                elif reply.content == "2":
                    name_sheet.delete_rows(i)
                    await ctx.send(f"❌ Denied request for **{old_name}**")

                # EDIT
                elif reply.content == "3":
                    await ctx.send("✏️ Send corrected format:\n`OldName NewName`")

                    edit = await bot.wait_for("message", timeout=60)
                    parts = edit.content.split()

                    if len(parts) != 2:
                        await ctx.send("❌ Invalid format. Skipped.")
                        continue

                    name_sheet.update_cell(i, 2, parts[0])
                    name_sheet.update_cell(i, 3, parts[1])
                    name_sheet.update_cell(i, 4, "Pending")

                    await ctx.send("💾 Edit saved (still pending).")

            except asyncio.TimeoutError:
                await ctx.send("⏳ Timed out — moving on.")

        await ctx.send("📋 Finished reviewing name changes.")

    except Exception as e:
        await ctx.send("❌ Error reviewing name changes.")
        print(f"Error in reviewnames: {e}")

# ============================
# TRANSLATE COMMAND (2‑STEP)
# ============================

LANG_OPTIONS = {
    1: ("English", "en"),
    2: ("Spanish", "es"),
    3: ("French", "fr"),
    4: ("German", "de"),
    5: ("Portuguese", "pt"),
    6: ("Japanese", "ja"),
    7: ("Korean", "ko"),
    8: ("Chinese (Simplified)", "zh-cn"),
}

pending_translations = {}  # user_id -> text_to_translate


@bot.command(name="translate")
async def translate_step1(ctx, *, text=None):
    """
    Step 1: User provides text OR replies to a message.
    Usage: !translate "Hello"
           (or reply to a message) !translate
    """

    # If no text was typed, check if user replied to a message
    if not text:
        if ctx.message.reference:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text = replied_msg.content
        else:
            await ctx.send("❌ Please include text to translate OR reply to a message.\nExample: `!translate \"Hello\"`")
            return

    # Save text for this user
    pending_translations[ctx.author.id] = text

    # Build menu
    menu = "**What language do you want this translated into?**\n\n"
    for num, (name, code) in LANG_OPTIONS.items():
        menu += f"{num} — {name}\n"

    embed = discord.Embed(
        title="🌍 Translation Menu",
        description=menu,
        color=0x00aaff
    )
    embed.set_footer(text="Type the number of the language you want.")

    await ctx.send(embed=embed)

# ============================
# TIMEZONE CONVERSION SYSTEM
# ============================

# Full timezone list
TIMEZONES = {
    # North America
    1: ("EST", "Eastern Standard Time", "America/Panama"),       # UTC-5, no DST
    2: ("EDT", "Eastern Daylight Time", "America/New_York"),     # UTC-4 with DST
    3: ("CST", "Central Standard Time", "America/Guatemala"),    # UTC-6, no DST
    4: ("CDT", "Central Daylight Time", "America/Chicago"),      # UTC-5 with DST
    5: ("MST", "Mountain Standard Time", "America/Phoenix"),     # UTC-7, no DST
    6: ("MDT", "Mountain Daylight Time", "America/Denver"),      # UTC-6 with DST
    7: ("PST", "Pacific Standard Time", "Pacific/Pitcairn"),     # UTC-8, no DST
    8: ("PDT", "Pacific Daylight Time", "America/Los_Angeles"),  # UTC-7 with DST
    9:  ("UTC", "Coordinated Universal Time", "UTC"),
    10: ("GMT", "Greenwich Mean Time", "Europe/London"),
    # Europe
    11: ("CET", "Central European Time", "Europe/Berlin"),       # UTC+1 (uses DST to CEST)
    12: ("CEST", "Central European Summer Time", "Europe/Berlin"),
    13: ("EET", "Eastern European Time", "Europe/Helsinki"),     # UTC+2 (uses DST to EEST)
    14: ("EEST", "Eastern European Summer Time", "Europe/Helsinki"),
    # Asia
    15: ("IST", "India Standard Time", "Asia/Kolkata"),          # UTC+5:30
    16: ("PKT", "Pakistan Standard Time", "Asia/Karachi"),       # UTC+5
    17: ("BST", "Bangladesh Standard Time", "Asia/Dhaka"),       # UTC+6
    18: ("WIB", "Western Indonesia Time", "Asia/Jakarta"),       # UTC+7
    19: ("WITA", "Central Indonesia Time", "Asia/Makassar"),     # UTC+8
    20: ("WIT", "Eastern Indonesia Time", "Asia/Jayapura"),      # UTC+9
    21: ("CST-CHINA", "China Standard Time", "Asia/Shanghai"),   # UTC+8
    22: ("JST", "Japan Standard Time", "Asia/Tokyo"),            # UTC+9
    23: ("KST", "Korea Standard Time", "Asia/Seoul"),            # UTC+9
    # Europe / Middle East
    24: ("MSK", "Moscow Standard Time", "Europe/Moscow"),        # UTC+3
    25: ("TRT", "Turkey Time", "Europe/Istanbul"),               # UTC+3
    26: ("AST", "Arabia Standard Time", "Asia/Riyadh"),          # UTC+3
    # Australia / NZ
    27: ("AEST", "Australian Eastern Standard Time", "Pacific/Port_Moresby"),  # UTC+10, no DST
    28: ("AEDT", "Australian Eastern Daylight Time", "Australia/Sydney"),      # UTC+11 with DST
    29: ("ACST", "Australian Central Standard Time", "Australia/Darwin"),      # UTC+9:30, no DST
    30: ("ACDT", "Australian Central Daylight Time", "Australia/Adelaide"),    # UTC+10:30 with DST
    31: ("AWST", "Australian Western Standard Time", "Australia/Perth"),       # UTC+8, no DST
    32: ("NZST", "New Zealand Standard Time", "Pacific/Tarawa"),               # UTC+12, no DST
    33: ("NZDT", "New Zealand Daylight Time", "Pacific/Auckland"),             # UTC+13 with DST
}

TZ_LOOKUP = {}
for num, (short, full, zone) in TIMEZONES.items():
    TZ_LOOKUP[str(num)] = num
    TZ_LOOKUP[short.lower()] = num
    TZ_LOOKUP[full.lower()] = num
    TZ_LOOKUP[short.lower().replace("-", "")] = num
    TZ_LOOKUP[full.lower().replace(" ", "")] = num

pending_conversions = {}  # user_id -> {"time": ..., "step": 1/2, "from": ...}


def parse_time_string(t):
    """Parses 12h or 24h time formats."""
    formats = ["%I:%M %p", "%I %p", "%H:%M", "%H"]
    for f in formats:
        try:
            return datetime.strptime(t, f)
        except:
            pass
    return None


@bot.command(name="convert")
async def convert_step1(ctx, *, time_str=None):
    """
    Step 1: User provides a time.
    Example: !convert 10:40 PM
    """

    # No time provided
    if not time_str:
        await ctx.send("❌ Please provide a time.\nExample: `!convert 10:40 PM`")
        return

    # Parse the time (12h or 24h)
    parsed = parse_time_string(time_str)
    if not parsed:
        await ctx.send(
            "❌ Invalid time format.\nTry formats like:\n"
            "`10:40 PM`, `22:40`, `7 PM`, `07:00`"
        )
        return

    # Save conversion state for this user
    pending_conversions[ctx.author.id] = {
        "time": parsed,
        "step": 1,
        "from": None
    }

    # Build timezone menu
    menu_lines = ["**What timezone is this time IN?**\n"]
    for num, (short, full, _) in TIMEZONES.items():
        menu_lines.append(f"{num}. **{short}** ({full})")

    embed = discord.Embed(
        title="🕒 Timezone Selection",
        description="\n".join(menu_lines),
        color=0x00aaff
    )
    embed.set_footer(text="Type the number or the timezone name.")

    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    content_raw = message.content.strip()
    content = content_raw.lower()

    # ============================================================
    # 1. TRANSLATE FLOW
    # ============================================================
    if user_id in pending_translations:
        if content.isdigit():
            choice = int(content)

            if choice in LANG_OPTIONS:
                lang_name, lang_code = LANG_OPTIONS[choice]
                original_text = pending_translations.pop(user_id)

                clean_text = (
                    original_text
                    .replace("!", "")
                    .replace("?", "")
                    .replace("\n", " ")
                    .strip()
                )

                try:
                    result = translator.translate(clean_text, dest=lang_code)
                except:
                    try:
                        result = translator.translate(clean_text.lower(), dest=lang_code)
                    except:
                        await message.channel.send("❌ Translation failed twice. Try rephrasing the text.")
                        return

                embed = discord.Embed(
                    title=f"🌐 Translated to {lang_name}",
                    color=0x00ff99
                )
                embed.add_field(name="🔤 Original", value=original_text, inline=False)
                embed.add_field(name="✨ Translation", value=result.text, inline=False)
                embed.set_footer(text=f"Detected language: {result.src}")

                await message.channel.send(embed=embed)
                return

        await message.channel.send("❌ Please type a valid number from the list.")
        return

    # ============================================================
    # 2. TIMEZONE CONVERSION FLOW
    # ============================================================
    if user_id in pending_conversions:
        data = pending_conversions[user_id]

        tz_choice = TZ_LOOKUP.get(content)
        if not tz_choice:
            await message.channel.send("❌ Invalid timezone. Type a number or timezone name.")
            return

        # STEP 1: Source timezone
        if data["step"] == 1:
            data["from"] = tz_choice
            data["step"] = 2

            menu = "**Convert this time INTO which timezone?**\n\n"
            for num, (short, full, _) in TIMEZONES.items():
                menu += f"{num}. **{short}** ({full})\n"

            embed = discord.Embed(
                title="🌍 Target Timezone",
                description=menu,
                color=0x00aaff
            )
            embed.set_footer(text="Type the number or the timezone name.")

            await message.channel.send(embed=embed)
            return

        # STEP 2: Target timezone
        elif data["step"] == 2:
            from_tz = TIMEZONES[data["from"]][2]
            to_tz = TIMEZONES[tz_choice][2]

            src = pytz.timezone(from_tz)
            dst = pytz.timezone(to_tz)

            # --------------------------------------------------------
            # FIX: Attach today's date to avoid historical offsets
            # --------------------------------------------------------
            now = datetime.now()
            dt = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=data["time"].hour,
                minute=data["time"].minute
            )

            original = src.localize(dt)
            converted = original.astimezone(dst)

            del pending_conversions[user_id]

            embed = discord.Embed(
                title="⏱️ Time Conversion Result",
                color=0x00ff99
            )
            embed.add_field(
                name="Original",
                value=f"{original.strftime('%I:%M %p')} {TIMEZONES[data['from']][0]}",
                inline=False
            )
            embed.add_field(
                name="Converted",
                value=f"{converted.strftime('%I:%M %p')} {TIMEZONES[tz_choice][0]}",
                inline=False
            )

            await message.channel.send(embed=embed)
            return

    # ============================================================
    # 3. Allow commands to run normally
    # ============================================================
    await bot.process_commands(message)

# === MAIN EXECUTION ===
if __name__ == "__main__":
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        print("❌ BOT_TOKEN missing")
        exit(1)

    print("🤖 Starting Discord bot...")
    bot.run(bot_token)
