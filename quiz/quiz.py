import json

from redbot.core import commands, Config
from redbot.core import checks

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.config = Config.get_conf(self)

    @commands.command(name='start')
    async def start_quiz(self, ctx):
        await self.start_vraag(ctx)

    async def start_vraag(self, ctx):
        vraag = random.choice(list(self.vragen['vragen'].keys()))
        antwoorden = self.vragen['vragen'][vraag]
        embed = discord.Embed(title=f"{vraag}", description="Klik op een van de knoppen om je antwoord te geven", color=0x00ff00)
        for i, antwoord in enumerate(antwoorden):
            embed.add_field(name=f"Antwoord {i+1}", value=antwoord, inline=False)
        message = await ctx.send(embed=embed)

        for i, antwoord in enumerate(antwoorden):
            await message.add_reaction(f":{chr(65+i)}:")

        def check(reaction, user):
            return str(user) == str(ctx.author) and reaction.message.id == message.id

        try:
            reaction = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except discord.ext.commands.CommandInvokeError:
            pass

        if reaction.reaction.emoji in [f":{chr(65+i)}:" for i in range(len(antwoorden))]:
            antwoord_num = ord(reaction.reaction.emoji.name) - 65
            if antwoorden[antwoord_num] == self.vragen['vragen'][vraag]['juist']:
                await ctx.send("Juist!")
                ctx.author.score += 1
            else:
                await ctx.send("Niet juist...")
        else:
            await ctx.send("Je hebt geen antwoord gegeven!")

    @commands.command(name='score', aliases=['scores'])
    async def toon_score(self, ctx):
        if ctx.author.id == ctx.guild.owner_id:
            scores = sorted([(author.id, author.score) for author in ctx.guild.members], key=lambda x: x[1], reverse=True)
            embed = discord.Embed(title="Scores", description="", color=0x00ff00)
            for i, (author_id, score) in enumerate(scores):
                member = ctx.guild.get_member(author_id)
                if member:
                    embed.add_field(name=f"Rang {i+1}", value=f"{member.name} - {score} punten", inline=False)
        else:
            score = ctx.author.score
            await ctx.send(f"Je hebt {score} punten!")

    @commands.command(name='top10')
    async def toon_top_10(self, ctx):
        scores = sorted([(author.id, author.score) for author in ctx.guild.members], key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="Top 10", description="", color=0x00ff00)
        for i, (author_id, score) in enumerate(scores):
            member = ctx.guild.get_member(author_id)
            if member:
                embed.add_field(name=f"Rang {i+1}", value=f"{member.name} - {score} punten", inline=False)
        await ctx.send(embed=embed)
