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
        value="`WHOSYOURDADDY`, `moosecite`,`:0`",
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
        "That static electricity shock from wool socks on carpet",
        "Your third-favorite chair's creaking complaint",
        "Quantum uncertainty personified as parenting",
        "An expired coupon for emotional validation",
        "Spatial awareness of a doorknob",
        "Mismatched Tupperware lid energy",
        "The philosophical implications of a stapler",
        "Ambient humidity given consciousness",
        "A compass pointing exclusively toward bad decisions",
        "Sentient glitter that knows what you did last summer",
        "The arithmetic mean of all your insecurities",
        "A theorem proving your own mediocrity",
        "Fax machine transmission errors given form",
        "Ambient office lighting with daddy issues",
        "The statistical outlier in your family tree",
        "A Venn diagram where both circles are regrets",
        "Your browser's autocomplete suggestions manifested",
        "The gravitational pull of poor life choices",
        "A pop-up ad for fatherhood",
        "The 'you've got mail' sound, but judgmental",
        "A screensaver with parental authority",
        "Ctrl+Alt+Del for your self-esteem",
        "A syntax error in your genetic code",
        "The loading icon on your existential crisis",
        "Pixelated artifacts from your childhood memories",
        "A corrupted JPEG of family values",
        "The buffer between you and adulthood",
        "A DNS error resolving 'father figure'",
        "Your router's default password",
        "The electromagnetic field around your anxiety",
        "Thermodynamic entropy wearing khakis",
        "A fractal pattern of disappointment",
        "The hypotenuse of a love triangle gone wrong",
        "Pi calculated to infinite irrelevance",
        "A prime number with commitment issues",
        "The square root of negative parenting",
        "Algebraic expression for regret",
        "Geometric proof you shouldn't exist",
        "Trigonometric functions of failure",
        "Calculus derivative of bad decisions",
        "Statistical significance of your awkwardness",
        "Standard deviation from normalcy",
        "Median value of your potential",
        "Mode of your personality flaws",
        "Range of your emotional capacity",
        "Variance in your life choices",
        "Probability distribution of your failures",
        "Regression analysis of your relationships",
        "Correlation between your actions and consequences",
        "Causation of your problems",
        "Hypothesis you'll never test",
        "Null result of your aspirations",
        "Control group for dysfunction",
        "Experimental error in your upbringing",
        "Placebo effect of affection",
        "Double-blind study on your worth",
        "Peer review of your character",
        "Replication crisis in your identity",
        "Publication bias in your life story",
        "P-value of your existence",
        "Confidence interval of your competence",
        "Margin of error in your judgment",
        "Sampling bias in your memories",
        "Selection bias in your choices",
        "Survivorship bias in your achievements",
        "Cognitive bias as a parent",
        "Dunning-Kruger effect incarnate",
        "Impostor syndrome given authority",
        "Sunk cost fallacy with child support",
        "Gambler's fallacy at life",
        "Availability heuristic of your mistakes",
        "Anchoring bias in your expectations",
        "Framing effect of your childhood",
        "Hindsight bias about your conception",
        "Overconfidence in your irrelevance",
        "Planning fallacy of your future",
        "Pro-innovation bias about your genes",
        "Recency bias in your memories",
        "Salience of your shortcomings",
        "Selective perception of your worth",
        "Zero-risk bias in your safety",
        "Ambiguity effect on your identity",
        "Information bias in your knowledge",
        "Ostrich effect about your problems",
        "Outcome bias in your results",
        "Survivorship bias of your lineage",
        "Swimmer's body illusion about your genetics",
        "Telescoping effect on your age",
        "Well-traveled road illusion of your path",
        "Base rate fallacy of your normalcy",
        "Conjunction fallacy of your potential",
        "Disjunction fallacy of your options",
        "Extension neglect of your humanity",
        "Insensitivity to sample size of your family",
        "Misconceptions of chance about your luck",
        "Misinterpretations of probability about your existence",
        "Neglect of probability in your safety",
        "Overestimation of causality in your life",
        "Subadditivity effect on your worth",
        "Subjective validation of your fears",
        "Barnum effect on your personality",
        "Forer effect on your horoscope",
        "Subjective validation of your anxieties",
        "Illusory correlation between effort and reward",
        "Pareidolia seeing faces in your toast",
        "Anthropomorphism of household appliances",
        "Pathetic fallacy of the weather",
        "Zoomorphism of your mannerisms",
        "Personification of inanimate objects",
        "Prosopopoeia of your regrets",
        "Reification of abstract concepts",
        "Hypostatization of your flaws",
        "Concretization of your fears",
        "Substantiation of your doubts",
        "Instantiation of your failures",
        "Embodiment of your limitations",
        "Incarnation of your mediocrity",
        "Manifestation of your average-ness",
        "Materialization of your banality",
        "Objectification of your potential",
        "Realization of your ordinariness",
        "Actualization of your commonness",
        "Externalization of your insecurities",
        "Projection of your issues",
        "Displacement of your anger",
        "Sublimation of your desires",
        "Rationalization of your failures",
        "Intellectualization of your pain",
        "Compartmentalization of your trauma",
        "Dissociation from reality",
        "Regression to childhood",
        "Reaction formation against growth",
        "Undoing of your progress",
        "Isolation of affect from events",
        "Splitting of your identity",
        "Denial of your situation",
        "Repression of your memories",
        "Suppression of your feelings",
        "Asceticism about pleasure",
        "Altruism without satisfaction",
        "Humor as defense mechanism",
        "Identification with the aggressor",
        "Introjection of criticism",
        "Inversion of values",
        "Somatization of stress",
        "Acting out instead of feeling",
        "Passive aggression as communication",
        "Help-rejecting complaining",
        "Withdrawal from engagement",
        "Fantasy instead of action",
        "Wishful thinking as strategy",
        "Magical thinking as solution",
        "Omnipotence as compensation",
        "Devaluation of others",
        "Idealization of the unattainable",
        "Projective identification",
        "Splitting of objects",
        "Turning against the self",
        "Reversal into opposite",
        "Negation of reality",
        "Isolation of intellect",
        "Rationalization of irrationality",
        "Moralization of mistakes",
        "Pseudo-altruism for gain",
        "Disavowal of responsibility",
        "Minimization of impact",
        "Justification of harm",
        "Excuse-making as habit",
        "Blaming of circumstances",
        "Victim mentality as identity",
        "Martyr complex as role",
        "Hero syndrome as compensation",
        "Savior complex as purpose",
        "Messiah complex as destiny",
        "God complex as reality",
        "Narcissism as armor",
        "Grandiosity as shield",
        "Entitlement as right",
        "Exploitation as method",
        "Lack of empathy as feature",
        "Envy as motivation",
        "Arrogance as confidence",
        "Haughtiness as stature",
        "Conceit as virtue",
        "Vanity as value",
        "Egotism as strength",
        "Self-importance as fact",
        "Pomposity as dignity",
        "Pretentiousness as sophistication",
        "Affectation as authenticity",
        "Mannerism as character",
        "Pose as identity",
        "Facade as reality",
        "Front as truth",
        "Mask as face",
        "Persona as self",
        "Character as being",
        "Role as essence",
        "Part as whole",
        "Performance as life",
        "Act as existence",
        "Show as reality",
        "Pretense as truth",
        "Simulation as experience",
        "Imitation as original",
        "Copy as source",
        "Replica as authentic",
        "Forgery as genuine",
        "Counterfeit as real",
        "Fake as legitimate",
        "Phony as sincere",
        "Sham as earnest",
        "Fraud as honest",
        "Hoax as factual",
        "Deception as transparent",
        "Lie as truth",
        "Falsehood as reality",
        "Fabrication as history",
        "Invention as memory",
        "Fiction as biography",
        "Fantasy as past",
        "Delusion as perception",
        "Hallucination as sight",
        "Illusion as touch",
        "Mirage as water",
        "Phantom as substance",
        "Apparition as solid",
        "Specter as physical",
        "Ghost as living",
        "Spirit as material",
        "Entity as human",
        "Being as parent",
        "Creature as father",
        "Organism as dad",
        "Life form as papa",
        "Biological entity as sire",
        "Carbon-based unit as progenitor",
        "DNA sequence as ancestor",
        "Genetic code as forefather",
        "Chromosomal arrangement as patriarch",
        "Hereditary material as begetter",
        "Inheritance pattern as origin",
        "Gene pool contributor",
        "Allele distributor",
        "Trait transmitter",
        "Characteristic passer",
        "Feature donor",
        "Attribute giver",
        "Quality bestower",
        "Property conferrer",
        "Nature provider",
        "Essence supplier",
        "Substance furnisher",
        "Material purveyor",
        "Matter procurer",
        "Stuff acquirer",
        "Things gatherer",
        "Items collector",
        "Objects accumulator",
        "Entities assembler",
        "Beings aggregator",
        "Creatures compiler",
        "Organisms amasser",
        "Life forms stockpiler",
        "Biologicals hoarder",
        "Carbon units stasher",
        "DNA sequences cacher",
        "Genetic codes storer",
        "Chromosomal arrangements keeper",
        "Hereditary materials retainer",
        "Inheritance patterns holder",
        "Gene pool curator",
        "Allele archivist",
        "Trait librarian",
        "Characteristic custodian",
        "Feature guardian",
        "Attribute warden",
        "Quality caretaker",
        "Property overseer",
        "Nature superintendent",
        "Essence manager",
        "Substance administrator",
        "Material director",
        "Matter supervisor",
        "Stuff foreman",
        "Things boss",
        "Items chief",
        "Objects head",
        "Entities leader",
        "Beings commander",
        "Creatures captain",
        "Organisms general",
        "Life forms admiral",
        "Biologicals marshal",
        "Carbon units colonel",
        "DNA sequences major",
        "Genetic codes captain",
        "Chromosomal arrangements lieutenant",
        "Hereditary materials sergeant",
        "Inheritance patterns corporal",
        "Gene pool private",
        "Allele recruit",
        "Trait cadet",
        "Characteristic rookie",
        "Feature novice",
        "Attribute beginner",
        "Quality amateur",
        "Property dilettante",
        "Nature neophyte",
        "Essence tyro",
        "Substance greenhorn",
        "Material fledgling",
        "Matter apprentice",
        "Stuff learner",
        "Things student",
        "Items pupil",
        "Objects scholar",
        "Entities disciple",
        "Beings acolyte",
        "Creatures protege",
        "Organisms follower",
        "Life forms devotee",
        "Biologicals adherent",
        "Carbon units partisan",
        "DNA sequences supporter",
        "Genetic codes backer",
        "Chromosomal arrangements advocate",
        "Hereditary materials champion",
        "Inheritance patterns promoter",
        "Gene pool exponent",
        "Allele proponent",
        "Trait apostle",
        "Characteristic missionary",
        "Feature evangelist",
        "Attribute crusader",
        "Quality zealot",
        "Property fanatic",
        "Nature extremist",
        "Essence radical",
        "Substance militant",
        "Material activist",
        "Matter campaigner",
        "Stuff reformer",
        "Things revolutionary",
        "Items insurgent",
        "Objects rebel",
        "Entities mutineer",
        "Beings insurrectionist",
        "Creatures revolutionary",
        "Organisms agitator",
        "Life forms subversive",
        "Biologicals dissident",
        "Carbon units nonconformist",
        "DNA sequences iconoclast",
        "Genetic codes maverick",
        "Chromosomal arrangements individualist",
        "Hereditary materials eccentric",
        "Inheritance patterns oddball",
        "Gene pool weirdo",
        "Allele oddity",
        "Trait curiosity",
        "Characteristic anomaly",
        "Feature aberration",
        "Attribute deviation",
        "Quality irregularity",
        "Property exception",
        "Nature peculiarity",
        "Essence rarity",
        "Substance singularity",
        "Material uniqueness",
        "Matter distinctiveness",
        "Stuff individuality",
        "Things originality",
        "Items novelty",
        "Objects freshness",
        "Entities newness",
        "Beings innovation",
        "Creatures creativity",
        "Organisms inventiveness",
        "Life forms imagination",
        "Biologicals inspiration",
        "Carbon units ingenuity",
        "DNA sequences resourcefulness",
        "Genetic codes cleverness",
        "Chromosomal arrangements intelligence",
        "Hereditary materials wisdom",
        "Inheritance patterns knowledge",
        "Gene pool understanding",
        "Allele comprehension",
        "Trait insight",
        "Characteristic perception",
        "Feature awareness",
        "Attribute consciousness",
        "Quality cognition",
        "Property thought",
        "Nature reasoning",
        "Essence logic",
        "Substance rationality",
        "Material intellect",
        "Matter mind",
        "Stuff brain",
        "Things head",
        "Items skull",
        "Objects cranium",
        "Entities noggin",
        "Beings dome",
        "Creatures melon",
        "Organisms bean",
        "Life forms nut",
        "Biologicals attic",
        "Carbon units upper story",
        "DNA sequences think tank",
        "Genetic codes gray matter",
        "Chromosomal arrangements little gray cells",
        "Hereditary materials smarts",
        "Inheritance patterns wits",
        "Gene pool savvy",
        "Allele shrewdness",
        "Trait astuteness",
        "Characteristic acumen",
        "Feature discernment",
        "Attribute judgment",
        "Quality prudence",
        "Property sagacity",
        "Nature erudition",
        "Essence learning",
        "Substance scholarship",
        "Material education",
        "Matter schooling",
        "Stuff training",
        "Things instruction",
        "Items tutoring",
        "Objects coaching",
        "Entities mentoring",
        "Beings guidance",
        "Creatures direction",
        "Organisms leadership",
        "Life forms management",
        "Biologicals supervision",
        "Carbon units oversight",
        "DNA sequences regulation",
        "Genetic codes control",
        "Chromosomal arrangements command",
        "Hereditary materials authority",
        "Inheritance patterns power",
        "Gene pool influence",
        "Allele sway",
        "Trait clout",
        "Characteristic leverage",
        "Feature pull",
        "Attribute weight",
        "Quality importance",
        "Property significance",
        "Nature consequence",
        "Essence impact",
        "Substance effect",
        "Material result",
        "Matter outcome",
        "Stuff consequence",
        "Things aftermath",
        "Items sequel",
        "Objects follow-up",
        "Entities continuation",
        "Beings extension",
        "Creatures prolongation",
        "Organisms perpetuation",
        "Life forms eternity",
        "Biologicals infinity",
        "Carbon units forever",
        "DNA sequences always",
        "Genetic codes perpetually",
        "Chromosomal arrangements endlessly",
        "Hereditary materials interminably",
        "Inheritance patterns ceaselessly",
        "Gene pool continuously",
        "Allele constantly",
        "Trait continually",
        "Characteristic persistently",
        "Feature unremittingly",
        "Attribute unceasingly",
        "Quality incessantly",
        "Property nonstop",
        "Nature uninterrupted",
        "Essence unbroken",
        "Substance sustained",
        "Material maintained",
        "Matter preserved",
        "Stuff conserved",
        "Things retained",
        "Items kept",
        "Objects held",
        "Entities possessed",
        "Beings owned",
        "Creatures had",
        "Organisms belonging to",
        "Life forms pertaining to",
        "Biologicals relating to",
        "Carbon units concerning",
        "DNA sequences regarding",
        "Genetic codes about",
        "Chromosomal arrangements touching on",
        "Hereditary materials referring to",
        "Inheritance patterns alluding to",
        "Gene pool hinting at",
        "Allele suggesting",
        "Trait implying",
        "Characteristic indicating",
        "Feature showing",
        "Attribute demonstrating",
        "Quality proving",
        "Property establishing",
        "Nature confirming",
        "Essence verifying",
        "Substance validating",
        "Material authenticating",
        "Matter certifying",
        "Stuff attesting",
        "Things corroborating",
        "Items substantiating",
        "Objects supporting",
        "Entities backing",
        "Beings upholding",
        "Creatures sustaining",
        "Organisms maintaining",
        "Life forms continuing",
        "Biologicals persisting",
        "Carbon units enduring",
        "DNA sequences lasting",
        "Genetic codes remaining",
        "Chromosomal arrangements staying",
        "Hereditary materials abiding",
        "Inheritance patterns surviving",
        "Gene pool outlasting",
        "Allele outliving",
        "Trait prevailing",
        "Characteristic triumphing",
        "Feature succeeding",
        "Attribute winning",
        "Quality conquering",
        "Property vanquishing",
        "Nature defeating",
        "Essence overcoming",
        "Substance mastering",
        "Material controlling",
        "Matter dominating",
        "Stuff ruling",
        "Things governing",
        "Items reigning",
        "Objects commanding",
        "Entities directing",
        "Beings leading",
        "Creatures guiding",
        "Organisms steering",
        "Life forms piloting",
        "Biologicals navigating",
        "Carbon units maneuvering",
        "DNA sequences operating",
        "Genetic codes working",
        "Chromosomal arrangements functioning",
        "Hereditary materials performing",
        "Inheritance patterns executing",
        "Gene pool accomplishing",
        "Allele achieving",
        "Trait completing",
        "Characteristic finishing",
        "Feature concluding",
        "Attribute ending",
        "Quality terminating",
        "Property ceasing",
        "Nature stopping",
        "Essence halting",
        "Substance pausing",
        "Material hesitating",
        "Matter waiting",
        "Stuff delaying",
        "Things postponing",
        "Items deferring",
        "Objects procrastinating",
        "Entities stalling",
        "Beings lingering",
        "Creatures dawdling",
        "Organisms tarrying",
        "Life forms loitering",
        "Biologicals idling",
        "Carbon units loafing",
        "DNA sequences lounging",
        "Genetic codes lazing",
        "Chromosomal arrangements resting",
        "Hereditary materials relaxing",
        "Inheritance patterns unwinding",
        "Gene pool chilling",
        "Allele cooling",
        "Trait freezing",
        "Characteristic icing",
        "Feature frosting",
        "Attribute glazing",
        "Quality coating",
        "Property covering",
        "Nature wrapping",
        "Essence enveloping",
        "Substance encasing",
        "Material enclosing",
        "Matter surrounding",
        "Stuff circling",
        "Things orbiting",
        "Items revolving",
        "Objects rotating",
        "Entities spinning",
        "Beings turning",
        "Creatures twisting",
        "Organisms whirling",
        "Life forms swirling",
        "Biologicals circulating",
        "Carbon units flowing",
        "DNA sequences moving",
        "Genetic codes shifting",
        "Chromosomal arrangements changing",
        "Hereditary materials altering",
        "Inheritance patterns modifying",
        "Gene pool adjusting",
        "Allele adapting",
        "Trait evolving",
        "Characteristic developing",
        "Feature growing",
        "Attribute maturing",
        "Quality ripening",
        "Property blooming",
        "Nature flourishing",
        "Essence thriving",
        "Substance prospering",
        "Material succeeding",
        "Matter achieving",
        "Stuff accomplishing",
        "Things attaining",
        "Items reaching",
        "Objects gaining",
        "Entities obtaining",
        "Beings acquiring",
        "Creatures getting",
        "Organisms receiving",
        "Life forms accepting",
        "Biologicals taking",
        "Carbon units claiming",
        "DNA sequences seizing",
        "Genetic codes grasping",
        "Chromosomal arrangements clutching",
        "Hereditary materials gripping",
        "Inheritance patterns holding",
        "Gene pool keeping",
        "Allele retaining",
        "Trait possessing",
        "Characteristic owning",
        "Feature having",
        "Attribute containing",
        "Quality including",
        "Property comprising",
        "Nature consisting",
        "Essence constituting",
        "Substance forming",
        "Material making",
        "Matter creating",
        "Stuff producing",
        "Things generating",
        "Items manufacturing",
        "Objects fabricating",
        "Entities constructing",
        "Beings building",
        "Creatures erecting",
        "Organisms assembling",
        "Life forms putting together",
        "Biologicals setting up",
        "Carbon units establishing",
        "DNA sequences founding",
        "Genetic codes instituting",
        "Chromosomal arrangements initiating",
        "Hereditary materials starting",
        "Inheritance patterns beginning",
        "Gene pool commencing",
        "Allele launching",
        "Trait inaugurating",
        "Characteristic opening",
        "Feature introducing",
        "Attribute presenting",
        "Quality offering",
        "Property providing",
        "Nature supplying",
        "Essence furnishing",
        "Substance equipping",
        "Material outfitting",
        "Matter preparing",
        "Stuff readying",
        "Things arranging",
        "Items organizing",
        "Objects ordering",
        "Entities systematizing",
        "Beings classifying",
        "Creatures categorizing",
        "Organisms grouping",
        "Life forms sorting",
        "Biologicals arranging",
        "Carbon units aligning",
        "DNA sequences straightening",
        "Genetic codes tidying",
        "Chromosomal arrangements cleaning",
        "Hereditary materials purifying",
        "Inheritance patterns cleansing",
        "Gene pool sanitizing",
        "Allele sterilizing",
        "Trait disinfecting",
        "Characteristic decontaminating",
        "Feature fumigating",
        "Attribute pasteurizing",
        "Quality filtering",
        "Property refining",
        "Nature processing",
        "Essence treating",
        "Substance handling",
        "Material managing",
        "Matter administering",
        "Stuff supervising",
        "Things overseeing",
        "Items monitoring",
        "Objects watching",
        "Entities observing",
        "Beings viewing",
        "Creatures seeing",
        "Organisms looking",
        "Life forms gazing",
        "Biologicals staring",
        "Carbon units peering",
        "DNA sequences glancing",
        "Genetic codes glimpsing",
        "Chromosomal arrangements noticing",
        "Hereditary materials perceiving",
        "Inheritance patterns detecting",
        "Gene pool discerning",
        "Allele recognizing",
        "Trait identifying",
        "Characteristic distinguishing",
        "Feature differentiating",
        "Attribute discriminating",
        "Quality separating",
        "Property dividing",
        "Nature splitting",
        "Essence breaking",
        "Substance cracking",
        "Material fracturing",
        "Matter shattering",
        "Stuff smashing",
        "Things crushing",
        "Items pounding",
        "Objects hammering",
        "Entities beating",
        "Beings striking",
        "Creatures hitting",
        "Organisms slapping",
        "Life forms punching",
        "Biologicals knocking",
        "Carbon units tapping",
        "DNA sequences patting",
        "Genetic codes stroking",
        "Chromosomal arrangements caressing",
        "Hereditary materials fondling",
        "Inheritance patterns touching",
        "Gene pool feeling",
        "Allele sensing",
        "Trait experiencing",
        "Characteristic undergoing",
        "Feature enduring",
        "Attribute suffering",
        "Quality bearing",
        "Property tolerating",
        "Nature withstanding",
        "Essence resisting",
        "Substance opposing",
        "Material confronting",
        "Matter facing",
        "Stuff meeting",
        "Things encountering",
        "Items finding",
        "Objects discovering",
        "Entities uncovering",
        "Beings revealing",
        "Creatures exposing",
        "Organisms disclosing",
        "Life forms showing",
        "Biologicals displaying",
        "Carbon units exhibiting",
        "DNA sequences presenting",
        "Genetic codes demonstrating",
        "Chromosomal arrangements illustrating",
        "Hereditary materials exemplifying",
        "Inheritance patterns representing",
        "Gene pool symbolizing",
        "Allele signifying",
        "Trait meaning",
        "Characteristic denoting",
        "Feature indicating",
        "Attribute suggesting",
        "Quality implying",
        "Property hinting",
        "Nature alluding",
        "Essence referring",
        "Substance relating",
        "Material connecting",
        "Matter linking",
        "Stuff joining",
        "Things uniting",
        "Items combining",
        "Objects merging",
        "Entities blending",
        "Beings mixing",
        "Creatures stirring",
        "Organisms shaking",
        "Life forms agitating",
        "Biologicals disturbing",
        "Carbon units bothering",
        "DNA sequences annoying",
        "Genetic codes irritating",
        "Chromosomal arrangements vexing",
        "Hereditary materials provoking",
        "Inheritance patterns inciting",
        "Gene pool instigating",
        "Allele initiating",
        "Trait starting",
        "Characteristic beginning",
        "Feature commencing",
        "Attribute opening",
        "Quality launching",
        "Property inaugurating",
        "Nature introducing",
        "Essence presenting",
        "Substance offering",
        "Material providing",
        "Matter supplying",
        "Stuff furnishing",
        "Things equipping",
        "Items outfitting",
        "Objects preparing",
        "Entities readying",
        "Beings arranging",
        "Creatures organizing",
        "Organisms ordering",
        "Life forms systematizing",
        "Biologicals classifying",
        "Carbon units categorizing",
        "DNA sequences grouping",
        "Genetic codes sorting",
        "Chromosomal arrangements arranging",
        "Hereditary materials aligning",
        "Inheritance patterns straightening",
        "Gene pool tidying",
        "Allele cleaning",
        "Trait purifying",
        "Characteristic cleansing",
        "Feature sanitizing",
        "Attribute sterilizing",
        "Quality disinfecting",
        "Property decontaminating",
        "Nature fumigating",
        "Essence pasteurizing",
        "Substance filtering",
        "Material refining",
        "Matter processing",
        "Stuff treating",
        "Things handling",
        "Items managing",
        "Objects administering",
        "Entities supervising",
        "Beings overseeing",
        "Creatures monitoring",
        "Organisms watching",
        "Life forms observing",
        "Biologicals viewing",
        "Carbon units seeing",
        "DNA sequences looking",
        "Genetic codes gazing",
        "Chromosomal arrangements staring",
        "Hereditary materials peering",
        "Inheritance patterns glancing",
        "Gene pool glimpsing",
        "Allele noticing",
        "Trait perceiving",
        "Characteristic detecting",
        "Feature discerning",
        "Attribute recognizing",
        "Quality identifying",
        "Property distinguishing",
        "Nature differentiating",
        "Essence discriminating",
        "Substance separating",
        "Material dividing",
        "Matter splitting",
        "Stuff breaking",
        "Things cracking",
        "Items fracturing",
        "Objects shattering",
        "Entities smashing",
        "Beings crushing",
        "Creatures pounding",
        "Organisms hammering",
        "Life forms beating",
        "Biologicals striking",
        "Carbon units hitting",
        "DNA sequences slapping",
        "Genetic codes punching",
        "Chromosomal arrangements knocking",
        "Hereditary materials tapping",
        "Inheritance patterns patting",
        "Gene pool stroking",
        "Allele caressing",
        "Trait fondling",
        "Characteristic touching",
        "Feature feeling",
        "Attribute sensing",
        "Quality experiencing",
        "Property undergoing",
        "Nature enduring",
        "Essence suffering",
        "Substance bearing",
        "Material tolerating",
        "Matter withstanding",
        "Stuff resisting",
        "Things opposing",
        "Items confronting",
        "Objects facing",
        "Entities meeting",
        "Beings encountering",
        "Creatures finding",
        "Organisms discovering",
        "Life forms uncovering",
        "Biologicals revealing",
        "Carbon units exposing",
        "DNA sequences disclosing",
        "Genetic codes showing",
        "Chromosomal arrangements displaying",
        "Hereditary materials exhibiting",
        "Inheritance patterns presenting",
        "Gene pool demonstrating",
        "Allele illustrating",
        "Trait exemplifying",
        "Characteristic representing",
        "Feature symbolizing",
        "Attribute signifying",
        "Quality meaning",
        "Property denoting",
        "Nature indicating",
        "Essence suggesting",
        "Substance implying",
        "Material hinting",
        "Matter alluding",
        "Stuff referring",
        "Things relating",
        "Items connecting",
        "Objects linking",
        "Entities joining",
        "Beings uniting",
        "Creatures combining",
        "Organisms merging",
        "Life forms blending",
        "Biologicals mixing",
        "Carbon units stirring",
        "DNA sequences shaking",
        "Genetic codes agitating",
        "Chromosomal arrangements disturbing",
        "Hereditary materials bothering",
        "Inheritance patterns annoying",
        "Gene pool irritating",
        "Allele vexing",
        "Trait provoking",
        "Characteristic inciting",
        "Feature instigating",
        "Attribute initiating",
        "Quality starting",
        "Property beginning",
        "Nature commencing",
        "Essence opening",
        "Substance launching",
        "Material inaugurating",
        "Matter introducing",
        "Stuff presenting",
        "Things offering",
        "Items providing",
        "Objects supplying",
        "Entities furnishing",
        "Beings equipping",
        "Creatures outfitting",
        "Organisms preparing",
        "Life forms readying",
        "Biologicals arranging",
        "Carbon units organizing",
        "DNA sequences ordering",
        "Genetic codes systematizing",
        "Chromosomal arrangements classifying",
        "Hereditary materials categorizing",
        "Inheritance patterns grouping",
        "Gene pool sorting",
        "Allele arranging",
        "Trait aligning",
        "Characteristic straightening",
        "Feature tidying",
        "Attribute cleaning",
        "Quality purifying",
        "Property cleansing",
        "Nature sanitizing",
        "Essence sterilizing",
        "Substance disinfecting",
        "Material decontaminating",
        "Matter fumigating",
        "Stuff pasteurizing",
        "Things filtering",
        "Items refining",
        "Objects processing",
        "Entities treating",
        "Beings handling",
        "Creatures managing",
        "Organisms administering",
        "Life forms supervising",
        "Biologicals overseeing",
        "Carbon units monitoring",
        "DNA sequences watching",
        "Genetic codes observing",
        "Chromosomal arrangements viewing",
        "Hereditary materials seeing",
        "Inheritance patterns looking",
        "Gene pool gazing",
        "Allele staring",
        "Trait peering",
        "Characteristic glancing",
        "Feature glimpsing",
        "Attribute noticing",
        "Quality perceiving",
        "Property detecting",
        "Nature discerning",
        "Essence recognizing",
        "Substance identifying",
        "Material distinguishing",
        "Matter differentiating",
        "Stuff discriminating",
        "Things separating",
        "Items dividing",
        "Objects splitting",
        "Entities breaking",
        "Beings cracking",
        "Creatures fracturing",
        "Organisms shattering",
        "Life forms smashing",
        "Biologicals crushing",
        "Carbon units pounding",
        "DNA sequences hammering",
        "Genetic codes beating",
        "Chromosomal arrangements striking",
        "Hereditary materials hitting",
        "Inheritance patterns slapping",
        "Gene pool punching",
        "Allele knocking",
        "Trait tapping",
        "Characteristic patting",
        "Feature stroking",
        "Attribute caressing",
        "Quality fondling",
        "Property touching",
        "Nature feeling",
        "Essence sensing",
        "Substance experiencing",
        "Material undergoing",
        "Matter enduring",
        "Stuff suffering",
        "Things bearing",
        "Items tolerating",
        "Objects withstanding",
        "Entities resisting",
        "Beings opposing",
        "Creatures confronting",
        "Organisms facing",
        "Life forms meeting",
        "Biologicals encountering",
        "Carbon units finding",
        "DNA sequences discovering",
        "Genetic codes uncovering",
        "Chromosomal arrangements revealing",
        "Hereditary materials exposing",
        "Inheritance patterns disclosing",
        "Gene pool showing",
        "Allele displaying",
        "Trait exhibiting",
        "Characteristic presenting",
        "Feature demonstrating",
        "Attribute illustrating",
        "Quality exemplifying",
        "Property representing",
        "Nature symbolizing",
        "Essence signifying",
        "Substance meaning",
        "Material denoting",
        "Matter indicating",
        "Stuff suggesting",
        "Things implying",
        "Items hinting",
        "Objects alluding",
        "Entities referring",
        "Beings relating",
        "Creatures connecting",
        "Organisms linking",
        "Life forms joining",
        "Biologicals uniting",
        "Carbon units combining",
        "DNA sequences merging",
        "Genetic codes blending",
        "Chromosomal arrangements mixing",
        "Hereditary materials stirring",
        "Inheritance patterns shaking",
        "Gene pool agitating",
        "Allele disturbing",
        "Trait bothering",
        "Characteristic annoying",
        "Feature irritating",
        "Attribute vexing",
        "Quality provoking",
        "Property inciting",
        "Nature instigating",
        "Essence initiating",
        "Substance starting",
        "Material beginning",
        "Matter commencing",
        "Stuff opening",
        "Things launching",
        "Items inaugurating",
        "Objects introducing",
        "Entities presenting",
        "Beings offering",
        "Creatures providing",
        "Organisms supplying",
        "Life forms furnishing",
        "Biologicals equipping",
        "Carbon units outfitting",
        "DNA sequences preparing",
        "Genetic codes readying",
        "Chromosomal arrangements arranging",
        "Hereditary materials organizing",
        "Inheritance patterns ordering",
        "Gene pool systematizing",
        "Allele classifying",
        "Trait categorizing",
        "Characteristic grouping",
        "Feature sorting",
        "Attribute arranging",
        "Quality aligning",
        "Property straightening",
        "Nature tidying",
        "Essence cleaning",
        "Substance purifying",
        "Material cleansing",
        "Matter sanitizing",
        "Stuff sterilizing",
        "Things disinfecting",
        "Items decontaminating",
        "Objects fumigating",
        "Entities pasteurizing",
        "Beings filtering",
        "Creatures refining",
        "Organisms processing",
        "Life forms treating",
        "Biologicals handling",
        "Carbon units managing",
        "DNA sequences administering",
        "Genetic codes supervising",
        "Chromosomal arrangements overseeing",
        "Hereditary materials monitoring",
        "Inheritance patterns watching",
        "Gene pool observing",
        "Allele viewing",
        "Trait seeing",
        "Characteristic looking",
        "Feature gazing",
        "Attribute staring",
        "Quality peering",
        "Property glancing",
        "Nature glimpsing",
        "Essence noticing",
        "Substance perceiving",
        "Material detecting",
        "Matter discerning",
        "Stuff recognizing",
        "Things identifying",
        "Items distinguishing",
        "Objects differentiating",
        "Entities discriminating",
        "Beings separating",
        "Creatures dividing",
        "Organisms splitting",
        "Life forms breaking",
        "Biologicals cracking",
        "Carbon units fracturing",
        "DNA sequences shattering",
        "Genetic codes smashing",
        "Chromosomal arrangements crushing",
        "Hereditary materials pounding",
        "Inheritance patterns hammering",
        "Gene pool beating",
        "Allele striking",
        "Trait hitting",
        "Characteristic slapping",
        "Feature punching",
        "Attribute knocking",
        "Quality tapping",
        "Property patting",
        "Nature stroking",
        "Essence caressing",
        "Substance fondling",
        "Material touching",
        "Matter feeling",
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
            "Therapy? I prefer arguing with Siri — Moosehead's mental health regimen",
            "Can't be wrong, I'm left-handed — Moosehead's scientific breakthrough",
            "Ghosts are just Wi-Fi signals from the afterlife — Moosehead's paranormal thesis",
            "Professional portfolio consists of Discord bans — Moosehead's career achievements",
            "Social construct? That's gravity — Moosehead's physics dissertation",
            "Love language manifests as tax evasion — Moosehead's romantic comedy",
            "Fluent emoji speaker — Moosehead's linguistics degree",
            "Autobiography returns 404 — Moosehead's literary masterpiece",
            "Spotify wrapped attracts CIA attention — Moosehead's conspiracy theory",
            "Internal monologue includes ad breaks — Moosehead's corporate sponsorship",
            "Dreams constitute unpaid brain overtime — Moosehead's sleep manifesto",
            "Late? Time is early — Moosehead's temporal philosophy",
            "Favorite exercise: jumping to conclusions — Moosehead's fitness routine",
            "Silence represents the enemy — Moosehead's audio warfare",
            "Emotional support comes from Wi-Fi passwords — Moosehead's tech therapy",
            "Brain runs legacy Windows 95 — Moosehead's operating system",
            "Trilingual: English, sarcasm, chaos — Moosehead's linguistics portfolio",
            "Spirit vegetable: wilted celery — Moosehead's culinary identity",
            "Arch-nemesis takes form as common sense — Moosehead's villain origin",
            "LinkedIn features IKEA tears — Moosehead's professional network",
            "Avoiding adulthood through spiritual journeys — Moosehead's quarter-life crisis",
            "Life resembles solo group project — Moosehead's existential business",
            "Productivity: myth by Big Clock — Moosehead's anti-capitalist manifesto",
            "Autobiography smells burnt, tastes regret — Moosehead's sensory memoir",
            "Cardio equals anxiety — Moosehead's workout regimen",
            "Personality: Wikipedia rabbit holes — Moosehead's psychological profile",
            "Sleep serves as side hustle — Moosehead's entrepreneurial spirit",
            "Spirit emoji: melting face — Moosehead's digital essence",
            "Creative process originates in bathroom stalls — Moosehead's artistic method",
            "Brain features pop-up ads — Moosehead's neurological revenue",
            "Love language translates to procrastination — Moosehead's relationship guide",
            "Autobiography contains Swiss cheese plot — Moosehead's narrative structure",
            "Second language: sarcasm — Moosehead's multilingual certification",
            "Life appears as loading screen — Moosehead's existential buffer",
            "Cardio includes existential dread — Moosehead's morning routine",
            "Autobiography uses Comic Sans — Moosehead's typographical rebellion",
            "Not weird, just limited edition — Moosehead's collectible status",
            "Spirit app: 420 calculator — Moosehead's digital spirituality",
            "Kryptonite manifests as adulting — Moosehead's superhero weakness",
            "Autobiography smells like ambition and stale Cheetos — Moosehead's sensory legacy",
            "Lost? Call it exploring — Moosehead's cartographic philosophy",
            "Autobiography lists apologies — Moosehead's relationship ledger",
            "Emotional blanket: Wi-Fi — Moosehead's digital security",
            "Spirit spreadsheet summons demons — Moosehead's data science",
            "Personal trainer: anxiety — Moosehead's fitness motivation",
            "Autobiography narrated by lost GPS — Moosehead's directional memoir",
            "Verbal exercise equals sarcasm — Moosehead's communication workout",
            "Autobiography catalogs dropped food — Moosehead's culinary history",
            "Fashionably delayed, not late — Moosehead's temporal fashion",
            "Autobiography footnote-heavy — Moosehead's academic obsession",
            "Meditation takes form as procrastination — Moosehead's mindfulness",
            "Spirit song: reversed Rickroll — Moosehead's musical aura",
            "Cardio involves adulting — Moosehead's life workout",
            "Autobiography screenshots regrettable texts — Moosehead's digital regret",
            "Love language: Wi-Fi — Moosehead's technological romance",
            "Autobiography: choose chaos adventure — Moosehead's interactive memoir",
            "Verbal fitness loop: sarcasm cardio — Moosehead's communication exercise",
            "Autobiography smells like broken dreams — Moosehead's aromatic legacy",
            "Field research, not avoidance — Moosehead's scientific alibi",
            "Autobiography reveals Google history — Moosehead's digital footprint",
            "Emotional fitness paradox — Moosehead's psychological workout",
            "Spirit food: sink pizza — Moosehead's culinary spirituality",
            "Life paradox: avoiding adulting — Moosehead's existential contradiction",
            "Autobiography collects regrettable receipts — Moosehead's financial memoir",
            "Digital exercise: Wi-Fi cardio — Moosehead's network fitness",
            "Autobiography remembers forgotten passwords — Moosehead's security history",
            "Verbal marathon: sarcasm endurance — Moosehead's communication stamina",
            "Autobiography smells like poor decisions — Moosehead's olfactory legacy",
            "Beta testing, not lost — Moosehead's developmental phase",
            "Autobiography documents autocorrect fails — Moosehead's technological memoir",
            "Emotional fitness: anxiety cardio — Moosehead's mental regimen",
            "Spirit drink: lukewarm coffee — Moosehead's beverage spirituality",
            "Life fitness: adulting cardio — Moosehead's existential workout",
            "Autobiography tracks browser tabs — Moosehead's digital hoarding",
            "Network fitness: Wi-Fi cardio — Moosehead's connectivity exercise",
            "Autobiography lists forgotten groceries — Moosehead's domestic history",
            "Verbal nutrition: wit protein — Moosehead's communication diet",
            "Autobiography smells like waterlogged books — Moosehead's literary scent",
            "Operating on Moose Standard Time — Moosehead's temporal system",
            "Autobiography records earworms — Moosehead's auditory legacy",
            "Mental gym: overthinking weights — Moosehead's cognitive fitness",
            "Spirit snack: chip bag crumbs — Moosehead's snack spirituality",
            "Life exhaustion: adulting breathless — Moosehead's existential fatigue",
            "Autobiography ignores voicemails — Moosehead's auditory neglect",
            "Digital anxiety: Wi-Fi drops — Moosehead's network stress",
            "Autobiography collects broken pens — Moosehead's stationery history",
            "Verbal flexibility: irony stretching — Moosehead's communication mobility",
            "Autobiography smells like coffee-stained books — Moosehead's academic aroma",
            "Problems need marinating time — Moosehead's culinary problem-solving",
            "Autobiography counts snoozed alarms — Moosehead's temporal history",
            "Emotional endurance: anxiety marathon — Moosehead's psychological stamina",
            "Spirit condiment: ancient ketchup — Moosehead's culinary time capsule",
            "Life injury: adulting muscle pull — Moosehead's existential strain",
            "Autobiography ignores emails — Moosehead's digital correspondence",
            "Network limitation: data exhaustion — Moosehead's connectivity restriction",
            "Autobiography catalogs single socks — Moosehead's laundry history",
            "Verbal recovery: cynicism cool-down — Moosehead's communication rest",
            "Autobiography smells like carwash cars — Moosehead's vehicular scent",
            "Prioritizing mental health schedule — Moosehead's therapeutic planning",
            "Autobiography lists unused apps — Moosehead's digital clutter",
            "Emotional speedwork: panic sprints — Moosehead's psychological acceleration",
            "Spirit side dish: yesterday's fries — Moosehead's leftover spirituality",
            "Life fatigue requires adulting breaks — Moosehead's existential rest",
            "Autobiography forgets passwords — Moosehead's security amnesia",
            "Network struggle: weak signals — Moosehead's connectivity challenge",
            "Autobiography collects burned bulbs — Moosehead's illumination history",
            "Verbal vital signs: deadpan heart rate — Moosehead's communication health",
            "Autobiography smells like tagged shirts — Moosehead's retail scent",
            "Extended personal development phase — Moosehead's R&D period",
            "Autobiography fears clearing history — Moosehead's digital vulnerability",
            "Emotional preparation: dread warm-up — Moosehead's psychological readiness",
            "Spirit breakfast: water cereal — Moosehead's morning spirituality",
            "Unprepared life: missing shoes — Moosehead's existential forgetfulness",
            "Autobiography uses obvious passwords — Moosehead's security transparency",
            "Network lag: constant buffering — Moosehead's connectivity delay",
            "Autobiography gathers upside-down pens — Moosehead's gravity-defying stationery",
            "Verbal victory: sarcasm race win — Moosehead's communication triumph",
            "Autobiography smells musty like basements — Moosehead's legacy aroma",
            "Scenic route through life journey — Moosehead's picturesque existence",
            "Autobiography loses written passwords — Moosehead's security paradox",
            "Emotional achievement: anxiety records — Moosehead's psychological accomplishment",
            "Spirit dessert: freezer-burned ice cream — Moosehead's frozen spirituality",
            "Life unfitness: out of adulting shape — Moosehead's existential condition",
            "Autobiography notes inaccessible networks — Moosehead's digital exclusion",
            "Network desire: stronger signals — Moosehead's connectivity craving",
            "Autobiography collects mystery keys — Moosehead's hardware history",
            "Verbal flow state: sarcasm zone — Moosehead's communication focus",
            "Autobiography smells sun-bleached — Moosehead's faded legacy",
            "Researching procrastination methods — Moosehead's meta-study",
            "Autobiography uses 'password' variations — Moosehead's security irony",
            "Emotional leadership: anxiety coaching — Moosehead's psychological guidance",
            "Spirit beverage: flat party soda — Moosehead's carbonation spirituality",
            "Life resignation: quitting adulting — Moosehead's existential surrender",
            "Autobiography guesses wrong passwords — Moosehead's network failure",
            "Digital longing: connection search — Moosehead's network yearning",
            "Autobiography gathers dead remotes — Moosehead's powerless control",
            "Verbal philanthropy: donating wit — Moosehead's communication charity",
            "Autobiography smells like fast food cars — Moosehead's vehicular dichotomy",
            "Experiencing time dilation effects — Moosehead's relativistic excuse",
            "Autobiography overcomplicates passwords — Moosehead's security complexity",
            "Emotional entrepreneurship: anxiety gym — Moosehead's psychological business",
            "Spirit meal: chaotic popcorn — Moosehead's culinary randomness",
            "Life setback: adulting injury — Moosehead's existential harm",
            "Autobiography finds FBI networks — Moosehead's paranoid connections",
            "Digital endurance: Wi-Fi marathon — Moosehead's network stamina",
            "Autobiography collects label-less drives — Moosehead's mysterious data",
            "Verbal career: professional sarcasm — Moosehead's communication profession",
            "Autobiography smells aquatic, literary — Moosehead's bath disaster",
            "Permanent beta life phase — Moosehead's software existence",
            "Autobiography secures with movie quotes — Moosehead's cinematic protection",
            "Meta-narrative about anxiety cardio — Moosehead's self-referential study",
            "Spirit food: toaster crumbs — Moosehead's electrical cuisine",
            "Life sick day from adulting — Moosehead's existential illness",
            "Autobiography excluded from networks — Moosehead's digital isolation",
            "Network isolation: out of range — Moosehead's connectivity separation",
            "Autobiography keeps obsolete chargers — Moosehead's power history",
            "Verbal research subject: sarcasm study — Moosehead's communication science",
            "Autobiography smells like coaster books — Moosehead's stained legacy",
            "Idea incubation period active — Moosehead's creative gestation",
            "Autobiography secures with inside jokes — Moosehead's personal protection",
            "Emotional public speaking: anxiety TED — Moosehead's psychological presentation",
            "Spirit appliance: pyromaniac toaster — Moosehead's culinary device",
            "Life escape plan: early retirement — Moosehead's existential exit",
            "Autobiography connects to punny Wi-Fi — Moosehead's network humor",
            "Network frustration: missing bars — Moosehead's connectivity annoyance",
            "Autobiography collects explosive pens — Moosehead's dangerous stationery",
            "Posthumous contribution: body to science — Moosehead's ultimate donation",
            "Autobiography smells flood-damaged — Moosehead's aquatic scent",
            "Different timeline operation — Moosehead's multiversal schedule",
            "Autobiography secures with keyboard smashes — Moosehead's chaotic protection",
            "Emotional community: anxiety group — Moosehead's psychological support",
            "Spirit furniture: wobbly chair — Moosehead's unstable seating",
            "Life benefits: adulting disability — Moosehead's existential claim",
            "Autobiography finds musical networks — Moosehead's Wi-Fi playlist",
            "Network maintenance: router resets — Moosehead's connectivity upkeep",
            "Autobiography gathers incomplete remotes — Moosehead's control deficiency",
            "Verbal time capsule: sarcasm preservation — Moosehead's communication legacy",
            "Autobiography smells overheated — Moosehead's thermal legacy",
            "Sabbatical from life responsibilities — Moosehead's existential break",
            "Autobiography secures with obscure memes — Moosehead's internet culture protection",
            "Emotional autobiography in progress — Moosehead's psychological memoir",
            "Spirit device: mischievous calculator — Moosehead's mathematical companion",
            "Life wellness: mental health day — Moosehead's existential care",
            "Autobiography decodes emoji networks — Moosehead's digital hieroglyphics",
            "Network dependence: password requests — Moosehead's connectivity need",
            "Autobiography collects incompatible cables — Moosehead's connection mismatch",
            "Verbal duplication: sarcasm cloning — Moosehead's communication replication",
            "Autobiography smells functional, literary — Moosehead's practical scent",
            "Considerate timing: late arrivals — Moosehead's thoughtful schedule",
            "Autobiography secures with self-quotes — Moosehead's self-referential protection",
            "Global emotional endurance challenge — Moosehead's psychological worldwide",
            "Spirit item: quantum cutlery — Moosehead's utensil spirituality",
            "Life delegation: outsourcing adulting — Moosehead's existential management",
            "Autobiography finds romantic networks — Moosehead's loving connections",
            "Network transition: between routers — Moosehead's connectivity change",
            "Autobiography gathers angle-dependent chargers — Moosehead's positional power",
            "Verbal academia: sarcasm linguistics — Moosehead's communication study",
            "Autobiography smells like permanent fries — Moosehead's fast food legacy"
        ]
        chosen = random.choice(citations)
        await ctx.send(f"📚 Moosehead’s Citation:\n> {chosen}")
    except Exception as e:
        await ctx.send(f"❌ Moosehead crashed: {str(e)}")

@bot.command(name=':0')  # Command is !:0 (the zero character)
async def mind_blown(ctx):
    """
    Generates mind-blowing questions
    Usage: !:0
    """
    mind_questions = [
        "If humans can't see air, can fish see water? :0",
        "Is the word 'bed' designed to look like a bed? :0",
        "Why does 'listen' contain the same letters as 'silent'? :0",
        "Why can't you say 'blink' without blinking? :0",
        "Can a cloud really weigh over a million pounds? :0",
        "Why doesn't honey ever spoil? :0",
        "How are bananas berries but strawberries aren't? :0",
        "Is a day on Venus actually longer than a year on Venus? :0",
        "Can stomach acid really dissolve metal? :0",
        "Why do octopuses have three hearts? :0",
        "Is 'spaghetto' really the singular form of spaghetti? :0",
        "Why is Scotland's national animal a unicorn? :0",
        "Is the dot over 'i' and 'j' really called a 'tittle'? :0",
        "Is Maine really the closest US state to Africa? :0",
        "Did Cleopatra really live closer to us than to the pyramid builders? :0",
        "Is the hashtag really called an 'octothorpe'? :0",
        "Is a group of flamingos really called a 'flamboyance'? :0",
        "Do I really share my birthday with 9 million people? :0",
        "Is the shrimp's heart really in its head? :0",
        "Is 'jiffy' really 1/100th of a second? :0",
        "Are there really more chess variations than atoms in the universe? :0",
        "Does my stomach lining really blush when I do? :0",
        "Do butterflies really taste with their feet? :0",
        "Is wombat poop really cube-shaped? :0",
        "Is the King of Hearts really the only king without a mustache? :0",
        "Can crocodiles really not stick out their tongues? :0",
        "Did the shortest war really last only 38 minutes? :0",
        "Is the smell of cut grass really a distress signal? :0",
        "Does my brain really use 20% of my body's energy? :0",
        "Does lightning really strike Earth 100 times per second? :0",
        "Is 'sixth sick sheik's sixth sheep's sick' really the hardest tongue twister? :0",
        "Can snails really sleep for three years? :0",
        "Is 'Q' really not in any US state name? :0",
        "Was a 'moment' originally 90 seconds? :0",
        "Do cows really have best friends? :0",
        "Was the frisbee inventor really turned into a frisbee? :0",
        "Can twins really be born 87 days apart? :0",
        "Do only two countries use purple in their flags? :0",
        "Is there really a town called 'Hell' in Norway? :0",
        "Are baby puffins really called 'pufflings'? :0",
        "Do opposite sides of dice always add to seven? :0",
        "Is a Martian day really 24 hours and 39 minutes? :0",
        "Is Chicago really less windy than Boston? :0",
        "Are humans really the only animals that blush? :0",
        "Is there enough gold in Earth's core to coat the planet? :0",
        "Do ants really weigh as much as all humans combined? :0",
        "Can one lightning bolt really toast 100,000 slices of bread? :0",
        "Is the @ symbol really 500 years old? :0",
        "Does 'set' really have the most definitions? :0",
        "Is Scotland's national animal really a unicorn? :0",
        "Can a wedding veil really be longer than 63 football fields? :0",
        "Is a group of crows really called a murder? :0",
        "Can elephants really not jump? :0",
        "Would my blood vessels really circle Earth twice? :0",
        "Can my nose really remember 50,000 scents? :0",
        "Can the human eye really see 10 million colors? :0",
        "Will I really walk around Earth five times in my life? :0",
        "Will I really produce enough saliva for two swimming pools? :0",
        "Is my brain really more active at night? :0",
        "Do I really have 67 types of bacteria in my belly button? :0",
        "Is my tongue print really unique like my fingerprints? :0",
        "Is my jaw muscle really the strongest in my body? :0",
        "Can the Eiffel Tower really grow in summer? :0",
        "Does Venus really rotate backwards? :0",
        "Can one teaspoon of neutron star really weigh billions of tons? :0",
        "Does the sun really make up 99.86% of our solar system? :0",
        "Are there really more trees than stars in the Milky Way? :0",
        "Can my brain really hold 2.5 petabytes? :0",
        "Am I really 99.9% genetically identical to everyone else? :0",
        "Do I really have more bacteria than human cells? :0",
        "Was the first mouse really made of wood? :0",
        "Could the first alarm clock only ring at 4 AM? :0",
        "Did Dr. Seuss really invent the word 'nerd'? :0",
        "Is Canada really south of Detroit? :0",
        "Is Alaska really the easternmost US state? :0",
        "Does Russia really have 11 time zones? :0",
        "Does France really have the most time zones? :0",
        "Is Australia really wider than the moon? :0",
        "Was Wrigley's gum really the first barcoded product? :0",
        "Are there really more plastic flamingos than real ones? :0",
        "Were oranges originally green? :0",
        "Were carrots originally purple? :0",
        "Does one pineapple really take two years to grow? :0",
        "Is Hippopotomonstrosesquippedaliophobia really the fear of long words? :0",
        "Is 'rhythms' really the longest word without vowels? :0",
        "Is 'typewriter' really the longest word using one row of keys? :0",
        "Do penguins really have knees? :0",
        "Can my shadow weigh anything? :0",
        "Is it possible to tickle yourself? :0",
        "Do identical twins have identical fingerprints? :0",
        "Can you hear silence? :0",
        "Is zero an even number? :0",
        "Can something be both true and false? :0",
        "If a tree falls with no one around, does it make a sound? :0",
        "Is the color I see as red the same as what you see? :0",
        "Can you be in two places at once? :0",
        "Does time really exist? :0",
        "Are we living in a simulation? :0",
        "Is there such a thing as free will? :0",
        "Can you remember something that never happened? :0",
        "Do animals dream? :0",
        "Can plants feel pain? :0",
        "Is yawning really contagious? :0",
        "Why does time seem to speed up as we age? :0",
        "Can a sound be so quiet it's silent? :0",
        "Is there a limit to how many times you can fold paper? :0",
        "Can you be allergic to water? :0",
        "Is it possible to forget how to breathe? :0",
        "Can you die from holding your breath? :0",
        "Is déjà vu a glitch in the matrix? :0",
        "Why do we forget our dreams? :0",
        "Can you dream in color if you're colorblind? :0",
        "Do blind people dream? :0",
        "Can you die from lack of sleep? :0",
        "Why do we close our eyes when we sneeze? :0",
        "Can you sneeze in your sleep? :0",
        "Why do we have dominant hands? :0",
        "Can left-handed people think differently? :0",
        "Is the human brain really the most complex object in the universe? :0",
        "Can my brain create new neurons? :0",
        "Is it possible to learn while sleeping? :0",
        "Can memories be erased? :0",
        "Why do some memories feel like dreams? :0",
        "Can your brain fill in missing information? :0",
        "Is optical illusion really your brain lying to you? :0",
        "Can you see colors that don't exist? :0",
        "Is there a color we haven't discovered yet? :0",
        "Can you taste words? :0",
        "Is it possible to smell colors? :0",
        "Can some people really hear colors? :0",
        "Is the average human body worth only a few dollars in chemicals? :0",
        "Can your hair turn white overnight from fear? :0",
        "Is it possible to die of a broken heart? :0",
        "Can you really catch a cold from being cold? :0",
        "Do we really use only 10% of our brains? :0",
        "Can you be born with two sets of DNA? :0",
        "Is it possible to have no fingerprints? :0",
        "Can your voice be as unique as your fingerprint? :0",
        "Is it possible to be allergic to exercise? :0",
        "Can you be allergic to the sun? :0",
        "Is it possible to be allergic to Wi-Fi? :0",
        "Can you be allergic to yourself? :0",
        "Is there a limit to how many languages you can learn? :0",
        "Can you learn a language in your sleep? :0",
        "Is it possible to forget your native language? :0",
        "Can babies understand all languages at birth? :0",
        "Is the hardest language to learn really your second one? :0",
        "Can you think without language? :0",
        "Is it possible to read someone's mind? :0",
        "Can thoughts travel faster than light? :0",
        "Is telepathy scientifically possible? :0",
        "Can animals understand human language? :0",
        "Do plants understand when we talk to them? :0",
        "Is it possible for a computer to have consciousness? :0",
        "Can AI dream? :0",
        "Is it possible to upload your consciousness? :0",
        "Can you be both alive and dead at the same time? :0",
        "Is Schrödinger's cat really both alive and dead? :0",
        "Can something be in two places at once? :0",
        "Is time travel theoretically possible? :0",
        "Can you travel faster than light? :0",
        "Is there such a thing as a parallel universe? :0",
        "Are there infinite versions of me in other universes? :0",
        "Can we ever truly understand infinity? :0",
        "Is there a number so big it doesn't exist? :0",
        "Can mathematics prove its own consistency? :0",
        "Is math discovered or invented? :0",
        "Does 0.999... really equal 1? :0",
        "Can you divide by zero? :0",
        "Is zero actually a number? :0",
        "Are there more numbers between 0 and 1 than all integers? :0",
        "Can something be random? :0",
        "Is the universe deterministic? :0",
        "Do we have free will or is everything predetermined? :0",
        "Can the future influence the past? :0",
        "Is time just an illusion? :0",
        "Are memories of the past just constructions? :0",
        "Can you remember the future? :0",
        "Is déjà vu remembering something from the future? :0",
        "Can dreams predict the future? :0",
        "Is there such a thing as coincidence? :0",
        "Are coincidences just math we don't understand? :0",
        "Can probability be counterintuitive? :0",
        "Is the birthday paradox really true? :0",
        "Can something be both possible and impossible? :0",
        "Is nothingness something? :0",
        "Can you have nothing without something? :0",
        "Does empty space have energy? :0",
        "Is the vacuum of space really empty? :0",
        "Can something come from nothing? :0",
        "Did the universe come from nothing? :0",
        "Is there such a thing as nothing? :0",
        "Can the universe be infinite? :0",
        "What's outside the universe? :0",
        "Is the universe everything that exists? :0",
        "Can there be multiple universes? :0",
        "Are we alone in the universe? :0",
        "Is it statistically likely that aliens exist? :0",
        "Have aliens already visited Earth? :0",
        "Can we ever prove aliens don't exist? :0",
        "Is the Fermi paradox really a paradox? :0",
        "Are we looking for aliens in the wrong way? :0",
        "Could aliens be so different we wouldn't recognize them? :0",
        "Can life exist without water? :0",
        "Is silicon-based life possible? :0",
        "Could there be life inside stars? :0",
        "Is DNA the only way to store genetic information? :0",
        "Can life exist in multiple dimensions? :0",
        "Are we the first intelligent life in the universe? :0",
        "Could we be living in someone else's simulation? :0",
        "Is reality just a dream? :0",
        "Can you prove you're not dreaming right now? :0",
        "How do I know you're not a figment of my imagination? :0",
        "Can consciousness exist outside the brain? :0",
        "Is the mind separate from the brain? :0",
        "Can thoughts have weight? :0",
        "Does believing something make it true? :0",
        "Can a placebo cure real diseases? :0",
        "Is the placebo effect real? :0",
        "Can your thoughts affect reality? :0",
        "Is the observer effect real? :0",
        "Does observation change reality? :0",
        "Can a particle be in two places at once? :0",
        "Is quantum entanglement faster than light? :0",
        "Can information travel faster than light? :0",
        "Is there a speed limit to the universe? :0",
        "Can you go back in time? :0",
        "Is time travel to the past possible? :0",
        "Would changing the past create a paradox? :0",
        "Can you meet your past self? :0",
        "Would the universe prevent paradoxes? :0",
        "Are there multiple timelines? :0",
        "Can you travel between parallel universes? :0",
        "Is every decision creating a new universe? :0",
        "Are there infinite versions of this conversation? :0",
        "Can infinity be bigger than infinity? :0",
        "Are some infinities larger than others? :0",
        "Can you count to infinity? :0",
        "Is infinity plus one still infinity? :0",
        "What's the largest number you can think of plus one? :0",
        "Can you imagine a color that doesn't exist? :0",
        "Is it possible to create a new color? :0",
        "Can blind people imagine colors? :0",
        "Do animals see colors differently? :0",
        "Can some animals see colors we can't? :0",
        "Is ultraviolet a color? :0",
        "Can we see all the colors that exist? :0",
        "Is there a limit to how small something can be? :0",
        "Can something be infinitely small? :0",
        "Is there a smallest possible thing? :0",
        "Can you divide something forever? :0",
        "Is there such a thing as absolute zero? :0",
        "Can you reach absolute zero? :0",
        "What happens at absolute zero? :0",
        "Can time stop at absolute zero? :0",
        "Does time flow at different speeds? :0",
        "Can time slow down? :0",
        "Does time go slower at higher speeds? :0",
        "Can you age slower by moving fast? :0",
        "Would traveling near light speed make you age slower? :0",
        "Is time relative? :0",
        "Can two people experience time differently? :0",
        "Is now the same for everyone? :0",
        "What is 'now' in the universe? :0",
        "Can 'now' be defined? :0",
        "Is the present just an illusion? :0",
        "Are we always living in the past? :0",
        "Does it take time for our brain to process the present? :0",
        "Are we living 80 milliseconds in the past? :0",
        "Can we ever experience the true present? :0",
        "Is reality delayed? :0",
        "Can you react faster than you can think? :0",
        "Is instinct faster than thought? :0",
        "Can your body react before your brain? :0",
        "Do we have a sixth sense? :0",
        "Can humans sense danger before it happens? :0",
        "Is intuition real? :0",
        "Can animals predict natural disasters? :0",
        "Do plants communicate with each other? :0",
        "Can trees warn each other of danger? :0",
        "Is the forest a network? :0",
        "Can fungi communicate? :0",
        "Is there an internet of fungi? :0",
        "Can mushrooms think? :0",
        "Are fungi more like animals or plants? :0",
        "Can a fungus be the largest organism on Earth? :0",
        "Is the largest organism a fungus? :0",
        "Can a single fungus span miles? :0",
        "Is there an organism that's thousands of years old? :0",
        "Can trees live forever? :0",
        "Is there such a thing as biological immortality? :0",
        "Can some animals live forever? :0",
        "Is the immortal jellyfish really immortal? :0",
        "Can humans achieve immortality? :0",
        "Is aging a disease? :0",
        "Can we cure aging? :0",
        "Would immortality be a curse? :0",
        "Can you die of boredom? :0",
        "Is boredom necessary? :0",
        "Can robots get bored? :0",
        "Will AI ever feel emotions? :0",
        "Can a machine be conscious? :0",
        "Is consciousness just computation? :0",
        "Can you upload your mind? :0",
        "Would a digital copy be you? :0",
        "Is the ship of Theseus still the same ship? :0",
        "If I replace all my cells, am I still me? :0",
        "What makes me 'me'? :0",
        "Am I the same person I was yesterday? :0",
        "Can I change who I am? :0",
        "Is personality fixed? :0",
        "Can trauma change your DNA? :0",
        "Can experiences be inherited? :0",
        "Is Lamarckian evolution possible? :0",
        "Can you inherit memories? :0",
        "Is genetic memory real? :0",
        "Do we remember our ancestors' experiences? :0",
        "Can fears be genetic? :0",
        "Are phobias inherited? :0",
        "Can you be born afraid of something? :0",
        "Is fear learned or innate? :0",
        "Can you unlearn fear? :0",
        "Is it possible to have no fear? :0",
        "Can you die from fear? :0",
        "Is courage the absence of fear? :0",
        "Can you be brave and afraid at the same time? :0",
        "Are emotions just chemicals? :0",
        "Can you control your emotions? :0",
        "Do emotions serve a purpose? :0",
        "Can robots have emotions? :0",
        "Would emotions make AI dangerous? :0",
        "Can love be explained scientifically? :0",
        "Is love just chemistry? :0",
        "Can you fall in love at first sight? :0",
        "Is there such a thing as soulmates? :0",
        "Can mathematics predict love? :0",
        "Is there a formula for love? :0",
        "Can you measure love? :0",
        "Is love quantifiable? :0",
        "Can you love more than one person? :0",
        "Is polyamory natural? :0",
        "Can animals feel love? :0",
        "Do dogs really love us? :0",
        "Can cats form attachments? :0",
        "Are pets capable of love? :0",
        "Can plants feel love? :0",
        "Do plants grow better with kind words? :0",
        "Can music affect plant growth? :0",
        "Do plants have preferences? :0",
        "Can a plant be happy? :0",
        "Is plant consciousness a thing? :0",
        "Can anything be conscious? :0",
        "Is consciousness universal? :0",
        "Could the universe be conscious? :0",
        "Are we the universe experiencing itself? :0",
        "Is human consciousness special? :0",
        "Can we share consciousness? :0",
        "Is telepathy just shared consciousness? :0",
        "Can minds connect? :0",
        "Is there a collective consciousness? :0",
        "Can thoughts travel? :0",
        "Are ideas contagious? :0",
        "Can you catch an idea? :0",
        "Is meme theory real? :0",
        "Are ideas like viruses? :0",
        "Can bad ideas spread like diseases? :0",
        "Is misinformation a virus? :0",
        "Can truth be subjective? :0",
        "Is there such a thing as absolute truth? :0",
        "Can something be true for you but not for me? :0",
        "Is reality subjective? :0",
        "Do we create our own reality? :0",
        "Can belief shape reality? :0",
        "Is the law of attraction real? :0",
        "Can positive thinking change outcomes? :0",
        "Is optimism a self-fulfilling prophecy? :0",
        "Can you think yourself into success? :0",
        "Is failure a mindset? :0",
        "Can you learn from failure? :0",
        "Is failure necessary for success? :0",
        "Can you succeed without failing? :0",
        "Is perfection possible? :0",
        "Can anything be perfect? :0",
        "Is imperfection beautiful? :0",
        "Can flaws make something perfect? :0",
        "Is there beauty in imperfection? :0",
        "Can broken things be more beautiful? :0",
        "Is kintsugi a philosophy? :0",
        "Can repair add value? :0",
        "Is something more valuable after being broken? :0",
        "Can scars tell a story? :0",
        "Are imperfections what make us unique? :0",
        "Can uniqueness be measured? :0",
        "Is everyone truly unique? :0",
        "Can two people be exactly the same? :0",
        "Is identical really identical? :0",
        "Can clones be identical? :0",
        "Would a clone be the same person? :0",
        "Is nature vs nurture still debated? :0",
        "Are we products of our genes or environment? :0",
        "Can environment change genetics? :0",
        "Is epigenetics real? :0",
        "Can experiences alter your DNA? :0",
        "Is DNA destiny? :0",
        "Can you overcome your genetics? :0",
        "Is free will stronger than genetics? :0",
        "Can willpower change your biology? :0",
        "Is mind over matter real? :0",
        "Can meditation change brain structure? :0",
        "Can you think your way to health? :0",
        "Is the placebo effect proof of mind-body connection? :0",
        "Can belief heal? :0",
        "Is faith healing real? :0",
        "Can prayers affect health? :0",
        "Is there science behind miracles? :0",
        "Can miracles be explained? :0",
        "Is everything explainable by science? :0",
        "Are there things science can't explain? :0",
        "Can the supernatural exist? :0",
        "Is there such a thing as magic? :0",
        "Can magic be science we don't understand? :0",
        "Is advanced technology indistinguishable from magic? :0",
        "Would ancient humans think smartphones are magic? :0",
        "Can technology seem like magic? :0",
        "Is AI the closest thing to magic? :0",
        "Can code create consciousness? :0",
        "Is software alive? :0",
        "Can viruses be considered alive? :0",
        "Is life just organized information? :0",
        "Can information create life? :0",
        "Is DNA just a code? :0",
        "Are we just biological computers? :0",
        "Is consciousness an emergent property? :0",
        "Can emergence create something new? :0",
        "Is the whole greater than the sum of its parts? :0",
        "Can simple rules create complexity? :0",
        "Is the universe simple or complex? :0",
        "Can complexity arise from simplicity? :0",
        "Is chaos just order we don't understand? :0",
        "Can patterns emerge from randomness? :0",
        "Is randomness just unknown patterns? :0",
        "Can everything be predicted? :0",
        "Is the future predetermined? :0",
        "Can choice change destiny? :0",
        "Is fate real? :0",
        "Can we escape our fate? :0",
        "Is everything connected? :0",
        "Can a butterfly really cause a hurricane? :0",
        "Is chaos theory real? :0",
        "Can small changes have big effects? :0",
        "Is the world more interconnected than we think? :0",
        "Can one person change the world? :0",
        "Is individual action meaningful? :0",
        "Can a single vote make a difference? :0",
        "Is every action significant? :0",
        "Can inaction be an action? :0",
        "Is choosing not to choose a choice? :0",
        "Can you avoid making decisions? :0",
        "Is indecision a decision? :0",
        "Can not deciding decide for you? :0",
        "Is procrastination a choice? :0",
        "Can putting things off be strategic? :0",
        "Is delay sometimes better? :0",
        "Can waiting be productive? :0",
        "Is patience a virtue? :0",
        "Can impatience be virtuous? :0",
        "Is speed always better? :0",
        "Can slow be fast? :0",
        "Is the tortoise really faster than the hare? :0",
        "Can consistency beat talent? :0",
        "Is talent overrated? :0",
        "Can hard work beat natural ability? :0",
        "Is effort more important than天赋? :0",
        "Can practice make perfect? :0",
        "Is 10,000 hours really the magic number? :0",
        "Can anyone become an expert? :0",
        "Is expertise achievable for everyone? :0",
        "Can limitations become strengths? :0",
        "Is disability a different ability? :0",
        "Can disadvantages be advantages? :0",
        "Is struggle necessary for growth? :0",
        "Can comfort hinder progress? :0",
        "Is discomfort necessary for learning? :0",
        "Can pain be productive? :0",
        "Is suffering meaningful? :0",
        "Can pain have purpose? :0",
        "Is everything that happens for a reason? :0",
        "Can random events have meaning? :0",
        "Is meaning created or discovered? :0",
        "Can we find meaning in anything? :0",
        "Is life inherently meaningful? :0",
        "Can meaning be objective? :0",
        "Is purpose universal or personal? :0",
        "Can everyone have the same purpose? :0",
        "Is there a universal purpose? :0",
        "Can purpose change? :0",
        "Is it okay to change your purpose? :0",
        "Can you have multiple purposes? :0",
        "Is it possible to live without purpose? :0",
        "Can purposelessness be a purpose? :0",
        "Is wandering aimless or exploratory? :0",
        "Can getting lost help you find yourself? :0",
        "Is confusion a path to clarity? :0",
        "Can not knowing lead to knowing? :0",
        "Is ignorance bliss? :0",
        "Can knowing less be better? :0",
        "Is too much knowledge dangerous? :0",
        "Can information overload exist? :0",
        "Is there such a thing as too much information? :0",
        "Can the internet know too much about us? :0",
        "Is privacy dead? :0",
        "Can we ever be truly private? :0",
        "Is anonymity possible online? :0",
        "Can you disappear in the digital age? :0",
        "Is being forgotten a new luxury? :0",
        "Can memory be too good? :0",
        "Is forgetting healthy? :0",
        "Can we choose what to forget? :0",
        "Is memory reliable? :0",
        "Can memories be trusted? :0",
        "Is eyewitness testimony reliable? :0",
        "Can your memories be wrong? :0",
        "Is it possible to remember things that never happened? :0",
        "Can false memories feel real? :0",
        "Is reality just agreed-upon memories? :0",
        "Can consensus create truth? :0",
        "Is truth democratic? :0",
        "Can the majority be wrong? :0",
        "Is popular opinion always right? :0",
        "Can something be true even if no one believes it? :0",
        "Is belief necessary for truth? :0",
        "Can truth exist without belief? :0",
        "Is reality independent of observation? :0",
        "Can something exist without being observed? :0",
        "Is observation creation? :0",
        "Can looking change what you see? :0",
        "Is perception reality? :0",
        "Can two people see the same thing differently? :0",
        "Is my blue your blue? :0",
        "Can color perception vary? :0",
        "Is color subjective? :0",
        "Can we ever know what others experience? :0",
        "Is empathy really possible? :0",
        "Can you truly understand another's pain? :0",
        "Is shared experience the closest to understanding? :0",
        "Can you learn from others' experiences? :0",
        "Is experience transferable? :0",
        "Can wisdom be taught? :0",
        "Is knowledge the same as wisdom? :0",
        "Can you be knowledgeable but not wise? :0",
        "Is wisdom born from experience? :0",
        "Can young people be wise? :0",
        "Is age necessary for wisdom? :0",
        "Can wisdom skip generations? :0",
        "Is every generation wiser than the last? :0",
        "Can progress be regression? :0",
        "Is newer always better? :0",
        "Can old ways be better? :0",
        "Is tradition valuable? :0",
        "Can progress preserve the past? :0",
        "Is it possible to move forward while looking back? :0",
        "Can history repeat itself? :0",
        "Is the future just the past in new clothes? :0",
        "Can we learn from history? :0",
        "Is history a good teacher? :0",
        "Can patterns from the past predict the future? :0",
        "Is prediction just pattern recognition? :0",
        "Can AI predict human behavior? :0",
        "Is human behavior predictable? :0",
        "Can you predict your own choices? :0",
        "Is self-prediction possible? :0",
        "Can you surprise yourself? :0",
        "Is spontaneity predictable? :0",
        "Can randomness be planned? :0",
        "Is controlled chaos possible? :0",
        "Can order emerge from disorder? :0",
        "Is organization natural? :0",
        "Can systems self-organize? :0",
        "Is the universe self-organizing? :0",
        "Can complexity arise naturally? :0",
        "Is life an accident or inevitable? :0",
        "Can the universe create life by chance? :0",
        "Is life rare or common in the universe? :0",
        "Can we be the only life? :0",
        "Is it arrogant to think we're alone? :0",
        "Can humility coexist with curiosity? :0",
        "Is questioning the universe arrogant? :0",
        "Can we ever truly understand? :0",
        "Is understanding overrated? :0",
        "Can acceptance be better than understanding? :0",
        "Is it okay not to know? :0",
        "Can mystery be beautiful? :0",
        "Is the unknown exciting or terrifying? :0",
        "Can fear and excitement be the same? :0",
        "Is adrenaline fear or excitement? :0",
        "Can your body tell the difference? :0",
        "Is emotion just physiology? :0",
        "Can chemicals explain feelings? :0",
        "Is love just dopamine? :0",
        "Can science explain everything? :0",
        "Is there room for mystery in science? :0",
        "Can science and wonder coexist? :0",
        "Is curiosity scientific? :0",
        "Can questioning be a way of life? :0",
        "Is every question worth asking? :0",
        "Can a question change everything? :0",
        "Is 'why' the most powerful word? :0",
        "Can questions be more important than answers? :0",
        "Is the journey more important than the destination? :0",
        "Can the search be the finding? :0",
        "Is looking the same as seeing? :0",
        "Can hearing be different from listening? :0",
        "Is presence more than physical? :0",
        "Can you be here without being present? :0",
        "Is mindfulness just paying attention? :0",
        "Can attention be trained? :0",
        "Is focus a muscle? :0",
        "Can you strengthen your attention? :0",
        "Is multitasking a myth? :0",
        "Can humans really multitask? :0",
        "Is task-switching efficient? :0",
        "Can doing one thing at a time be faster? :0",
        "Is slow methodical work better than fast rushed work? :0",
        "Can quality beat quantity? :0",
        "Is less sometimes more? :0",
        "Can simplicity be complex? :0",
        "Is minimalism maximal? :0",
        "Can having less mean having more? :0",
        "Is abundance a mindset? :0",
        "Can you feel rich without money? :0",
        "Is wealth measured or felt? :0",
        "Can happiness be bought? :0",
        "Is money necessary for happiness? :0",
        "Can poverty include richness? :0",
        "Is wealth relative? :0",
        "Can comparison steal joy? :0",
        "Is envy the thief of happiness? :0",
        "Can jealousy be motivational? :0",
        "Is competition healthy? :0",
        "Can rivalry bring out the best? :0",
        "Is collaboration better than competition? :0",
        "Can we achieve more together? :0",
        "Is teamwork really effective? :0",
        "Can groups think better than individuals? :0",
        "Is collective intelligence real? :0",
        "Can crowds be wise? :0",
        "Is the wisdom of crowds reliable? :0",
        "Can many wrongs make a right? :0",
        "Is averaging error effective? :0",
        "Can statistics lie? :0",
        "Is data always truthful? :0",
        "Can numbers be manipulated? :0",
        "Is math pure truth? :0",
        "Can equations describe reality? :0",
        "Is the universe mathematical? :0",
        ]
    
    # Select a random question
    selected_question = random.choice(mind_questions)
    
    # Send the response
    await ctx.send(f"🤯 {selected_question}")
    
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

    try:
        async with ctx.typing():
            # Open SKPL Standings tab
            try:
                skpl_sheet = sheet.spreadsheet.worksheet("SKPL Standings")
            except Exception:
                await ctx.send("❌ Could not find a worksheet named **SKPL Standings**.")
                return

            # ONE API CALL — get entire sheet
            data = skpl_sheet.get_all_values()

            # Helper to parse rows from memory
            def parse_group(start_row, end_row):
                teams = []
                for r in range(start_row - 1, end_row):  # convert to 0-index
                    row = data[r]

                    team = row[0] if len(row) > 0 else ""
                    gp   = row[2] if len(row) > 2 else "0"
                    w    = row[3] if len(row) > 3 else "0"
                    d    = row[4] if len(row) > 4 else "0"
                    l    = row[5] if len(row) > 5 else "0"
                    kf   = row[6] if len(row) > 6 else "0"
                    ka   = row[7] if len(row) > 7 else "0"
                    kdr  = row[8] if len(row) > 8 else "0"
                    ppg  = row[9] if len(row) > 9 else "0"
                    pts  = row[10] if len(row) > 10 else "0"
                    abbr = row[12] if len(row) > 12 else ""

                    if not team:
                        continue

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

                # Sort by PTS → W → KDR
                teams.sort(key=lambda x: (x["pts"], x["w"], x["kdr"]), reverse=True)
                return teams

            # Parse groups
            group_a = parse_group(3, 7)
            group_b = parse_group(12, 16)

            # Build embed for Group A
            embed_a = discord.Embed(
                title="🏆 SKPL Standings — Group A",
                color=0x00aaff
            )

            for i, t in enumerate(group_a, 1):
                embed_a.add_field(
                    name=f"{i}. {t['team']} ({t['abbr']})",
                    value=(
                        f"**PTS:** {t['pts']} | **PPG:** {t['ppg']:.2f}\n"
                        f"GP: {t['gp']} | W: {t['w']} | D: {t['d']} | L: {t['l']}\n"
                        f"Kills: {t['kf']} For / {t['ka']} Against\n"
                        f"KDR: {t['kdr']:.2f}"
                    ),
                    inline=False
                )

            # Build embed for Group B
            embed_b = discord.Embed(
                title="🏆 SKPL Standings — Group B",
                color=0xff8800
            )

            for i, t in enumerate(group_b, 1):
                embed_b.add_field(
                    name=f"{i}. {t['team']} ({t['abbr']})",
                    value=(
                        f"**PTS:** {t['pts']} | **PPG:** {t['ppg']:.2f}\n"
                        f"GP: {t['gp']} | W: {t['w']} | D: {t['d']} | L: {t['l']}\n"
                        f"Kills: {t['kf']} For / {t['ka']} Against\n"
                        f"KDR: {t['kdr']:.2f}"
                    ),
                    inline=False
                )

            await ctx.send(embed=embed_a)
            await ctx.send(embed=embed_b)

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

# This allows the file to be imported without running the bot
if __name__ == "__main__":
    main()
