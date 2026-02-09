
from redbot.core import commands, Config
import discord
import time

PURPLE = discord.Color.from_rgb(155, 89, 182)

class Confession(commands.Cog):
    """Anoniem biecht-kanaal met logging, cooldowns en filtering"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=934857234, force_registration=True)

        default_guild = {
            "confession_channel": None,
            "log_channel": None,
            "cooldown": 300,
            "badwords": [],
            "counter": 0
        }

        self.config.register_guild(**default_guild)
        self.user_cooldowns = {}

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def confession(self, ctx):
        """Instellingen voor het biecht-systeem"""
        pass

    @confession.command()
    async def setconfession(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).confession_channel.set(channel.id)
        await ctx.send(f"✅ Biecht-kanaal ingesteld op {channel.mention}")

    @confession.command()
    async def setlog(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"✅ Log-kanaal ingesteld op {channel.mention}")

    @confession.command()
    async def setcooldown(self, ctx, seconds: int):
        await self.config.guild(ctx.guild).cooldown.set(seconds)
        await ctx.send(f"⏱ Cooldown ingesteld op {seconds} seconden")

    @confession.command()
    async def addbadword(self, ctx, word: str):
        async with self.config.guild(ctx.guild).badwords() as bw:
            if word.lower() not in bw:
                bw.append(word.lower())
        await ctx.send(f"🚫 `{word}` toegevoegd aan blacklist")

    @confession.command()
    async def removebadword(self, ctx, word: str):
        async with self.config.guild(ctx.guild).badwords() as bw:
            if word.lower() in bw:
                bw.remove(word.lower())
        await ctx.send(f"♻ `{word}` verwijderd uit blacklist")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = await self.config.guild(message.guild).all()
        if message.channel.id != data["confession_channel"]:
            return

        now = time.time()
        last = self.user_cooldowns.get(message.author.id, 0)
        if now - last < data["cooldown"]:
            await message.delete()
            return

        for badword in data["badwords"]:
            if badword in message.content.lower():
                await message.delete()
                return

        self.user_cooldowns[message.author.id] = now

        counter = data["counter"] + 1
        await self.config.guild(message.guild).counter.set(counter)

        await message.delete()

        embed = discord.Embed(
            title=f"Biecht #{counter}",
            description=message.content or "*[Alleen bijlage]*",
            color=PURPLE
        )
        embed.set_footer(text="Anoniem")

        await message.channel.send(embed=embed)

        for attachment in message.attachments:
            await message.channel.send(file=await attachment.to_file())

        log_channel = message.guild.get_channel(data["log_channel"])
        if log_channel:
            log_embed = discord.Embed(
                title=f"Biecht #{counter}",
                description=message.content or "*[Alleen bijlage]*",
                color=discord.Color.dark_purple()
            )
            log_embed.add_field(
                name="Gebruiker",
                value=f"{message.author} ({message.author.id})",
                inline=False
            )
            await log_channel.send(embed=log_embed)
            for attachment in message.attachments:
                await log_channel.send(file=await attachment.to_file())

def setup(bot):
    bot.add_cog(Confession(bot))
