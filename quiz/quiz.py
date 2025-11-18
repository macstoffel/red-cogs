import json
import random
import asyncio

import discord
from redbot.core import commands

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        # Simple in-memory replacements for Redbot's Config and score tracking
        self.config = {}
        # Sample questions structure: vraag -> {'antwoorden': [...], 'juist': 'correct answer'}
        self.vragen = {
            "vragen": {
                "Wat is 2+2?": {"antwoorden": ["3", "4", "5"], "juist": "4"},
                "Kleur van de hemel?": {"antwoorden": ["Blauw", "Groen", "Rood"], "juist": "Blauw"}
            }
        }
        # scores stored as {user_id: score}
        self.scores = {}

    @commands.command(name='start')
    async def start_quiz(self, ctx):
        await self.start_vraag(ctx)

    async def start_vraag(self, ctx):
        vraag = random.choice(list(self.vragen['vragen'].keys()))
        data = self.vragen['vragen'][vraag]
        antwoorden = data['antwoorden']
        embed = discord.Embed(title=f"{vraag}", description="Klik op een van de knoppen om je antwoord te geven", color=0x00ff00)
        for i, antwoord in enumerate(antwoorden):
            embed.add_field(name=f"Antwoord {i+1}", value=antwoord, inline=False)
        message = await ctx.send(embed=embed)

        # Use numeric emojis for reactions
        emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i in range(len(antwoorden)):
            await message.add_reaction(emoji_list[i])

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Je hebt geen antwoord gegeven!")
            return

        if reaction.emoji in emoji_list[:len(antwoorden)]:
            antwoord_num = emoji_list.index(reaction.emoji)
            if antwoorden[antwoord_num] == data['juist']:
                await ctx.send("Juist!")
                self.scores[ctx.author.id] = self.scores.get(ctx.author.id, 0) + 1
            else:
                await ctx.send("Niet juist...")
        else:
            await ctx.send("Je hebt geen geldig antwoord gegeven!")

    @commands.command(name='score', aliases=['scores'])
    async def toon_score(self, ctx):
        if ctx.author.id == ctx.guild.owner_id:
            scores = sorted([(member.id, self.scores.get(member.id, 0)) for member in ctx.guild.members], key=lambda x: x[1], reverse=True)
            embed = discord.Embed(title="Scores", description="", color=0x00ff00)
            for i, (author_id, score) in enumerate(scores):
                member = ctx.guild.get_member(author_id)
                if member:
                    embed.add_field(name=f"Rang {i+1}", value=f"{member.name} - {score} punten", inline=False)
            await ctx.send(embed=embed)
        else:
            score = self.scores.get(ctx.author.id, 0)
            await ctx.send(f"Je hebt {score} punten!")

    @commands.command(name='top10')
    async def toon_top_10(self, ctx):
        scores = sorted([(member.id, self.scores.get(member.id, 0)) for member in ctx.guild.members], key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="Top 10", description="", color=0x00ff00)
        for i, (author_id, score) in enumerate(scores):
            member = ctx.guild.get_member(author_id)
            if member:
                embed.add_field(name=f"Rang {i+1}", value=f"{member.name} - {score} punten", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Quiz(bot))
