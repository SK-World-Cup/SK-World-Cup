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
