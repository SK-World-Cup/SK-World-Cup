import discord
from discord.ext import commands

class OneVOne(commands.Cog):
    def __init__(self, bot, sheet):
        self.bot = bot
        self.sheet = sheet

    @commands.command(name='playerelo', aliases=['stats', 'elo'])
    async def playerelo(self, ctx, *, player_name=None):
        # paste your existing playerelo logic here
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
        # paste your existing top10 logic here
        pass

def setup(bot):
    sheet = getattr(bot, "sheet", None)
    bot.add_cog(OneVOne(bot, sheet))
