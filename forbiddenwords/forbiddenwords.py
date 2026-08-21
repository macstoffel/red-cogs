import re
from datetime import datetime, timedelta

import discord
from redbot.core import commands, Config


PURPLE = discord.Color.purple()


class ForbiddenWords(commands.Cog):
    """Verboden woorden systeem met strafpunten."""

    def __init__(self, bot):
        self.bot = bot

        self.config = Config.get_conf(
            self,
            identifier=987654321123456,
            force_registration=True,
        )

        default_guild = {
            "forbidden_words": []
        }

        default_member = {
            "points": 0
        }

        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    async def purple_embed(self, title, description):
        return discord.Embed(
            title=title,
            description=description,
            color=PURPLE
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if not message.guild:
            return

        if message.author.bot:
            return

        words = await self.config.guild(message.guild).forbidden_words()

        if not words:
            return

        content = message.content.lower()

        triggered = None

        for word in words:
            pattern = rf"\b{re.escape(word.lower())}\b"

            if re.search(pattern, content):
                triggered = word
                break

        if not triggered:
            return

        member_conf = self.config.member(message.author)

        points = await member_conf.points()
        points += 1

        await member_conf.points.set(points)

        embed = discord.Embed(
            title="⚠️ Verboden Woord",
            description=(
                f"{message.author.mention} heeft het verboden woord "
                f"**{triggered}** gebruikt en krijgt **1 punt**.\n\n"
                f"**Totaal aantal punten:** {points}"
            ),
            color=PURPLE
        )

        await message.channel.send(embed=embed)

        if points % 10 == 0:

            try:
                timeout_until = datetime.utcnow() + timedelta(minutes=1)

                await message.author.edit(
                    timed_out_until=timeout_until,
                    reason="10 strafpunten bereikt"
                )

                embed = discord.Embed(
                    title="⛔ Timeout Uitgedeeld",
                    description=(
                        f"{message.author.mention} heeft "
                        f"**{points} punten** bereikt en krijgt een "
                        f"timeout van **1 minuut**."
                    ),
                    color=PURPLE
                )

                await message.channel.send(embed=embed)

            except discord.Forbidden:

                embed = discord.Embed(
                    title="❌ Fout",
                    description=(
                        "Ik heb onvoldoende rechten om een timeout uit te voeren."
                    ),
                    color=PURPLE
                )

                await message.channel.send(embed=embed)

    @commands.group(name="forbidden")
    @commands.guild_only()
    async def forbidden(self, ctx):
        """Verboden woorden systeem."""
        pass

    @forbidden.command(name="add")
    @commands.admin_or_permissions(manage_guild=True)
    async def add_word(self, ctx, *, word: str):

        word = word.lower()

        async with self.config.guild(ctx.guild).forbidden_words() as words:

            if word in words:

                embed = discord.Embed(
                    title="❌ Fout",
                    description="Dat woord staat al in de lijst.",
                    color=PURPLE
                )

                return await ctx.send(embed=embed)

            words.append(word)

        embed = discord.Embed(
            title="✅ Woord Toegevoegd",
            description=f"'{word}' is toegevoegd aan de verboden woorden.",
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @forbidden.command(name="remove")
    @commands.admin_or_permissions(manage_guild=True)
    async def remove_word(self, ctx, *, word: str):

        word = word.lower()

        async with self.config.guild(ctx.guild).forbidden_words() as words:

            if word not in words:

                embed = discord.Embed(
                    title="❌ Fout",
                    description="Dat woord staat niet in de lijst.",
                    color=PURPLE
                )

                return await ctx.send(embed=embed)

            words.remove(word)

        embed = discord.Embed(
            title="✅ Woord Verwijderd",
            description=f"'{word}' is verwijderd.",
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @forbidden.command(name="list")
    async def list_words(self, ctx):

        words = await self.config.guild(ctx.guild).forbidden_words()

        if not words:

            embed = discord.Embed(
                title="📖 Verboden Woorden",
                description="Er zijn geen verboden woorden ingesteld.",
                color=PURPLE
            )

            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="📖 Verboden Woorden",
            description="\n".join(f"• {word}" for word in words),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @forbidden.command(name="score")
    async def score(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        points = await self.config.member(member).points()

        embed = discord.Embed(
            title="📊 Strafpunten",
            description=(
                f"{member.mention} heeft momenteel "
                f"**{points} strafpunten**."
            ),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @forbidden.command(name="top10")
    async def top10(self, ctx):

        members = await self.config.all_members(ctx.guild)

        ranking = []

        for member_id, data in members.items():

            member = ctx.guild.get_member(member_id)

            if member:
                ranking.append(
                    (member, data.get("points", 0))
                )

        ranking.sort(key=lambda x: x[1], reverse=True)

        if not ranking:

            embed = discord.Embed(
                title="🏆 Top 10",
                description="Geen scores gevonden.",
                color=PURPLE
            )

            return await ctx.send(embed=embed)

        lines = []

        for i, (member, points) in enumerate(ranking[:10], start=1):
            lines.append(
                f"**{i}.** {member.display_name} • {points} punten"
            )

        embed = discord.Embed(
            title="🏆 Top 10 Strafpunten",
            description="\n".join(lines),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @forbidden.group(name="points")
    @commands.admin_or_permissions(manage_guild=True)
    async def points(self, ctx):
        """Puntenbeheer."""
        pass

    @points.command(name="set")
    async def points_set(
        self,
        ctx,
        member: discord.Member,
        amount: int,
    ):

        await self.config.member(member).points.set(amount)

        embed = discord.Embed(
            title="✅ Punten Ingesteld",
            description=(
                f"{member.mention} heeft nu "
                f"**{amount} punten**."
            ),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @points.command(name="add")
    async def points_add(
        self,
        ctx,
        member: discord.Member,
        amount: int,
    ):

        current = await self.config.member(member).points()

        current += amount

        await self.config.member(member).points.set(current)

        embed = discord.Embed(
            title="✅ Punten Toegevoegd",
            description=(
                f"{amount} punten toegevoegd aan "
                f"{member.mention}.\n\n"
                f"Nieuwe score: **{current}**"
            ),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @points.command(name="remove")
    async def points_remove(
        self,
        ctx,
        member: discord.Member,
        amount: int,
    ):

        current = await self.config.member(member).points()

        current = max(0, current - amount)

        await self.config.member(member).points.set(current)

        embed = discord.Embed(
            title="✅ Punten Verwijderd",
            description=(
                f"Nieuwe score van {member.mention}: "
                f"**{current} punten**"
            ),
            color=PURPLE
        )

        await ctx.send(embed=embed)

    @points.command(name="reset")
    async def points_reset(
        self,
        ctx,
        member: discord.Member,
    ):

        await self.config.member(member).points.set(0)

        embed = discord.Embed(
            title="✅ Punten Gereset",
            description=f"{member.mention} heeft nu 0 punten.",
            color=PURPLE
        )

        await ctx.send(embed=embed)