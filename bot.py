@bot.command(name='playerelo', aliases=['stats', 'elo'])
async def playerelo(ctx, *, player_name=None):
    if not player_name:
        await ctx.send("❌ Please provide a player name.")
        return
    if not sheet:
        await ctx.send("❌ Google Sheets connection failed.")
        return

    async with ctx.typing():
        data = sheet.get_all_records()
        player = next((p for p in data if p.get("Player", "").lower() == player_name.lower()), None)
        if not player:
            await ctx.send(f"❌ Player `{player_name}` not found.")
            return

        embed = discord.Embed(title=f"📊 Stats for {player['Player']}", color=0x00ff00)
        embed.add_field(name="🔢 Elo", value=player.get("Current Elo", "N/A"), inline=True)
        embed.add_field(name="🎮 Games", value=player.get("Games", "N/A"), inline=True)
        embed.add_field(name="📈 Record", value=player.get("Record", "N/A"), inline=True)
        embed.add_field(name="⚔️ K/D", value=player.get("K/D Ratio", "N/A"), inline=True)
        embed.add_field(name="🔥 Streak", value=player.get("Streak", "N/A"), inline=True)
        embed.set_footer(text="Data from 1v1 Rankings Sheet")
        await ctx.send(embed=embed)

@bot.command(name='top10')
async def top10(ctx):
    if not sheet:
        await ctx.send("❌ Google Sheets connection failed.")
        return
    async with ctx.typing():
        names = sheet.col_values(1)[1:]
        elos_raw = sheet.col_values(3)[1:]
        elos = [float(e) if e else 0.0 for e in elos_raw]
        top = sorted(zip(names, elos), key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🏆 Top 10 Elo", color=0x00ff00)
        for i, (name, elo) in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(name=f"{medal} {name}", value=f"Elo: {elo:.1f}", inline=False)
        await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx, *, player_name=None):
    if not player_name:
        await ctx.send("❌ Provide a player name.")
        return
    if not sheet:
        await ctx.send("❌ Google Sheets connection failed.")
        return
    async with ctx.typing():
        names = sheet.col_values(1)[1:]
        lower_names = [n.lower() for n in names]
        if player_name.lower() not in lower_names:
            await ctx.send(f"❌ `{player_name}` not found.")
            return
        rank = lower_names.index(player_name.lower()) + 1  # Adjust for 1-based rank
        await ctx.send(f"📊 `{player_name}` is ranked #{rank} in the spreadsheet.")

@bot.command(name='streaks')
async def streaks(ctx):
    if not sheet:
        await ctx.send("❌ Google Sheets connection failed.")
        return
    async with ctx.typing():
        names = sheet.col_values(1)[1:]
        streaks = sheet.col_values(11)[1:]  # Column K
        streak_pairs = []
        for name, streak in zip(names, streaks):
            try:
                streak_val = int(streak)
                streak_pairs.append((name, streak_val))
            except:
                continue
        top_streaks = sorted(streak_pairs, key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🔥 Top Win Streaks", color=0xff5733)
        for i, (name, streak) in enumerate(top_streaks, 1):
            embed.add_field(name=f"{i}. {name}", value=f"Streak: {streak}", inline=False)
        await ctx.send(embed=embed)

@bot.command(name='winrate')
async def winrate(ctx):
    if not sheet:
        await ctx.send("❌ Google Sheets connection failed.")
        return
    async with ctx.typing():
        names = sheet.col_values(1)[1:]
        winrates = sheet.col_values(6)[1:]  # Column F
        winrate_pairs = []
        for name, wr in zip(names, winrates):
            try:
                wr_val = float(wr.strip('%'))
                winrate_pairs.append((name, wr_val))
            except:
                continue
        top_wr = sorted(winrate_pairs, key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🏅 Top Win %", color=0x1abc9c)
        for i, (name, wr) in enumerate(top_wr, 1):
            embed.add_field(name=f"{i}. {name}", value=f"Win Rate: {wr:.1f}%", inline=False)
        await ctx.send(embed=embed)

