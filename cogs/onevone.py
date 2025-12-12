import discord
from discord.ext import commands

class OneVOne(commands.Cog):
    def __init__(self, bot, sheet):
        self.bot = bot
        self.sheet = sheet

    @commands.command(name='playerelo', aliases=['stats', 'elo'])
    async def playerelo(self, ctx, *, player_name=None):
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
        pass

    @commands.command(name='headtohead', aliases=['h2h'])
    async def headtohead(self, ctx, player1=None, player2=None):
        # paste your existing headtohead logic here
        pass

    @commands.command(name='gamesbyplayer')
    async def gamesbyplayer(self, ctx, *, player_name=None):
        # implement logic to fetch all games for a player
        pass

    @commands.command(name='top10')
    async def top10(self, ctx):
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
        pass

def setup(bot):
    sheet = getattr(bot, "sheet", None)
    bot.add_cog(OneVOne(bot, sheet))
