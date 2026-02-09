from redbot.core import commands, Config
import discord
import time

PURPLE = discord.Color.from_rgb(155, 89, 182)

class Confession(commands.Cog):
    """Anoniem biecht-kanaal met logging, cooldowns, embeds en settings overzicht"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_confession(
            identifier=934857234,
            force_registration=True
        )

        default_guild = {
            "confession_channel": None,
            "log_channel": None,
            "cooldown": 300,
            "badwords": [],
            "counter": 0
        }

        self.config.register_guild(**default_guild)
        self.user_cooldowns = {}

    # ---------------- CONFIG COMMANDS ---------------- #

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

    @confession.command(name="settings")
    @commands.admin_or_permissions(manage_guild=True)
    async def confession_settings(self, ctx):
        """Toont een overzicht van alle Confession instellingen"""

        data = await self.config.guild(ctx.guild).all()

        confession_channel = (
            f"<#{data['confession_channel']}>" if data["confession_channel"] else "❌ Niet ingesteld"
        )
        log_channel = (
            f"<#{data['log_channel']}>" if data["log_channel"] else "❌ Niet ingesteld"
        )

        cooldown = data["cooldown"]
        counter = data["counter"]
        badwords = ", ".join(data["badwords"]) if data["badwords"] else "Geen"

        embed = discord.Embed(
            title="⚙️ Confession – Instellingen",
            color=PURPLE
        )

        embed.add_field(name="📝 Biecht-kanaal", value=confession_channel, inline=False)
        embed.add_field(name="📜 Log-kanaal", value=log_channel, inline=False)
        embed.add_field(name="⏱ Cooldown", value=f"{cooldown} seconden", inline=False)
        embed.add_field(name="🔢 Biecht-teller", value=str(counter), inline=False)
        embed.add_field(name="🚫 Blacklist", value=badwords, inline=False)

        embed.set_footer(text=f"Opgevraagd door {ctx.author}")

        await ctx.send(embed=embed)

    # ---------------- LISTENERS ---------------- #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = await self.config.guild(message.guild).all()
        if message.channel.id != data["confession_channel"]:
            return

        # Cooldown check
        now = time.time()
        last = self.user_cooldowns.get(message.author.id, 0)
        if now - last < data["cooldown"]:
            await message.delete()
            return

        # Profanity filter
        lowered = message.content.lower()
        for badword in data["badwords"]:
            if badword in lowered:
                await message.delete()
                return

        self.user_cooldowns[message.author.id] = now

        # Counter
        counter = data["counter"] + 1
        await self.config.guild(message.guild).counter.set(counter)

        # Verwijder origineel bericht
        try:
            await message.delete()
        except discord.Forbidden:
            return

        # Anoniem embed
        anon_embed = discord.Embed(
            title=f"Biecht #{counter}",
            description=message.content or "*[Alleen bijlage]*",
            color=PURPLE
        )
        anon_embed.set_footer(text="Anoniem • Confessions")
        await message.channel.send(embed=anon_embed)

        # Bijlagen anoniem doorsturen
        for attachment in message.attachments:
            await message.channel.send(file=await attachment.to_file())

        # Logging
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

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if reaction.message.guild is None:
            return

        confession_channel = await self.config.guild(reaction.message.guild).confession_channel()
        if reaction.message.channel.id == confession_channel:
            try:
                await reaction.remove(user)
            except discord.Forbidden:
                pass

def setup(bot):
    bot.add_cog(Confession(bot))