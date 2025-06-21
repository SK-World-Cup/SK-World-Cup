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

@bot.event
async def on_guild_remove(guild):
    """Event triggered when bot leaves a server"""
    print(f"👋 Left server: {guild.name} (ID: {guild.id})")

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
