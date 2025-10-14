import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from flask import Flask
from threading import Thread

# === KEEP-ALIVE SERVER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

def run_server():
    """Run Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False)

# Start keep-alive server
Thread(target=run_server, daemon=True).start()

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

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
    """
    if not player1 or not player2:
        embed = discord.Embed(
            title="❌ Missing Player Names",
            description="Please provide two player names.\n**Usage:** `!headtohead <player1> <player2>`",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return
    
    if not gc:
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
            try:
                # Access the separate match history spreadsheet
                match_history_spreadsheet = gc.open("1v1 Match History")
                
                # Get the first worksheet or find a specific one
                match_sheet = None
                worksheets = match_history_spreadsheet.worksheets()
                
                # Try to find the main match history worksheet
                for ws in worksheets:
                    ws_name = ws.title.lower()
                    if any(keyword in ws_name for keyword in ['sheet1', 'match', 'history', 'game', 'record']):
                        match_sheet = ws
                        break
                
                # If no specific sheet found, use the first one
                if not match_sheet and worksheets:
                    match_sheet = worksheets[0]
                
                if not match_sheet:
                    embed = discord.Embed(
                        title="❌ Match History Sheet Not Found",
                        description="Could not find a match history worksheet in the '1v1 Match History' spreadsheet.",
                        color=0xff0000
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Get all match data
                # Column A = Player 1, Column B = Scores, Column C = Player 2
                player1_col = match_sheet.col_values(1)[1:]  # Skip header
                scores_col = match_sheet.col_values(2)[1:]   # Skip header  
                player2_col = match_sheet.col_values(3)[1:]  # Skip header
                
                # Find matches between the two players
                head_to_head_matches = []
                
                # Ensure all columns have the same length
                min_length = min(len(player1_col), len(scores_col), len(player2_col))
                
                for i in range(min_length):
                    p1 = str(player1_col[i]).strip() if i < len(player1_col) else ""
                    score = str(scores_col[i]).strip() if i < len(scores_col) else ""
                    p2 = str(player2_col[i]).strip() if i < len(player2_col) else ""
                    
                    # Check if this match involves both players
                    if ((p1.lower() == player1.lower() and p2.lower() == player2.lower()) or
                        (p1.lower() == player2.lower() and p2.lower() == player1.lower())):
                        
                        match_data = {
                            'player1': p1,
                            'score': score,
                            'player2': p2,
                            'row': i + 2  # +2 because we skipped header and are 0-indexed
                        }
                        head_to_head_matches.append(match_data)
                
                if not head_to_head_matches:
                    embed = discord.Embed(
                        title="🤷 No Matches Found",
                        description=f"No head-to-head matches found between `{player1}` and `{player2}`.",
                        color=0xffaa00
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Calculate wins
                player1_wins = 0
                player2_wins = 0
                draws = 0
                
                for match in head_to_head_matches:
                    score = match['score']
                    match_p1 = match['player1']
                    match_p2 = match['player2']
                    
                    # Parse score (assume format like "2-1", "3-0", etc.)
                    if '-' in score:
                        try:
                            score_parts = score.split('-')
                            score1 = int(score_parts[0].strip())
                            score2 = int(score_parts[1].strip())
                            
                            # Determine winner based on who's in player1 position for this match
                            if match_p1.lower() == player1.lower():
                                # player1 is in first position
                                if score1 > score2:
                                    player1_wins += 1
                                elif score2 > score1:
                                    player2_wins += 1
                                else:
                                    draws += 1
                            else:
                                # player1 is in second position (player2 in data)
                                if score2 > score1:
                                    player1_wins += 1
                                elif score1 > score2:
                                    player2_wins += 1
                                else:
                                    draws += 1
                        except (ValueError, IndexError):
                            # Can't parse score, skip this match for win counting
                            continue
                
                # Create embed
                embed = discord.Embed(
                    title=f"⚔️ Head-to-Head: {player1} vs {player2}",
                    description=f"**Overall Record:** {player1}: {player1_wins} - {player2}: {player2_wins}" + 
                               (f" - Draws: {draws}" if draws > 0 else ""),
                    color=0x0099ff
                )
                
                # Add recent matches (limit to 10 most recent)
                recent_matches = head_to_head_matches[-10:]  # Get last 10 matches
                recent_matches.reverse()  # Show most recent first
                
                if recent_matches:
                    match_history = ""
                    for i, match in enumerate(recent_matches, 1):
                        score = match['score']
                        match_p1 = match['player1'] 
                        match_p2 = match['player2']
                        
                        # Determine winner for display
                        winner = "Draw"
                        if '-' in score:
                            try:
                                score_parts = score.split('-')
                                score1 = int(score_parts[0].strip())
                                score2 = int(score_parts[1].strip())
                                
                                if score1 > score2:
                                    winner = match_p1
                                elif score2 > score1:
                                    winner = match_p2
                            except (ValueError, IndexError):
                                winner = "N/A"
                        
                        match_info = f"**{i}.** {match_p1} vs {match_p2} - {score}"
                        if winner != "N/A":
                            match_info += f" (Winner: **{winner}**)"
                        match_info += "\n"
                        
                        match_history += match_info
                    
                    embed.add_field(
                        name="📋 Recent Matches",
                        value=match_history,
                        inline=False
                    )
                
                # Add statistics
                total_matches = player1_wins + player2_wins + draws
                if total_matches > 0:
                    player1_winrate = (player1_wins / total_matches) * 100
                    player2_winrate = (player2_wins / total_matches) * 100
                    
                    embed.add_field(
                        name="📊 Win Rates",
                        value=f"{player1}: {player1_winrate:.1f}%\n{player2}: {player2_winrate:.1f}%",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎮 Total Matches",
                        value=str(total_matches),
                        inline=True
                    )
                
                embed.set_footer(text="Data from match history spreadsheet")
                await ctx.send(embed=embed)
                
            except Exception as sheet_error:
                print(f"❌ Match history sheet error: {str(sheet_error)}")
                embed = discord.Embed(
                    title="❌ Match History Access Error",
                    description="Could not access match history data. Make sure the match history sheet exists.",
                    color=0xff0000
                )
                embed.add_field(
                    name="💡 Expected Format",
                    value="Column A: Player 1\nColumn B: Scores (format: 2-1)\nColumn C: Player 2",
                    inline=False
                )
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
        name="1v1 rankings | !help_stats"
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
    import random

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


import random  # Make sure this is at the top of your file

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



# === MAIN EXECUTION ===
if __name__ == "__main__":
    # Get bot token from environment variables
    bot_token = os.getenv("BOT_TOKEN", "")

    if not bot_token:
        print("❌ Error: BOT_TOKEN not found in environment variables")
        print("Please set the BOT_TOKEN environment variable with your Discord bot token")
        exit(1)

    print("🚀 Starting Discord Bot...")
    print("🌐 Keep-alive server running on http://0.0.0.0:5000")

    try:
        # Run the bot
        bot.run(bot_token)
    except discord.LoginFailure:
        print("❌ Error: Invalid bot token. Please check your BOT_TOKEN environment variable.")
    except Exception as e:
        print(f"❌ Fatal error starting bot: {str(e)}")
