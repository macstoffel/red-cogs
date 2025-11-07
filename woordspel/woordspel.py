import discord
from discord.ext import commands
from redbot.core import commands as red_commands
from redbot.core.utils.chat_formatting import box

class Woordspel(red_commands.Cog):
    """Een woordketting spel voor Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.channel_id = None
        self.current_score = 0
        self.high_score = 0
        self.last_word = None
        self.last_user_id = None
        self.goal_points = 10

    @red_commands.command()
    async def start(self, ctx, goal: int = 10):
        """Start het woordspel."""
        if self.active:
            await ctx.send("Er is al een spel actief!")
            return
        self.active = True
        self.channel_id = ctx.channel.id
        self.current_score = 0
        self.last_word = None
        self.last_user_id = None
        self.goal_points = goal

        embed = discord.Embed(
            title="🎮 Woordspel gestart!",
            description=(
                f"Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n"
                f"Doel: {self.goal_points} punten\n\n"
                "Het spel begint nu! Typ je eerste woord."
            ),
            color=0x9b59b6  # Paarse kleur
        )
        await ctx.send(embed=embed)

    @red_commands.command()
    async def stop(self, ctx):
        """Stop het woordspel."""
        if not self.active:
            await ctx.send("Er is geen actief spel!")
            return
        self.active = False
        self.current_score = 0
        self.last_word = None
        self.last_user_id = None
        await ctx.send("Het woordspel is gestopt.")

    @red_commands.command()
    async def totaal(self, ctx):
        """Toon de huidige score."""
        await ctx.send(f"Huidige score: {self.current_score}")

    @red_commands.command()
    async def highscore(self, ctx):
        """Toon de hoogste behaalde score."""
        await ctx.send(f"Hoogste score ooit: {self.high_score}")

    @red_commands.Cog.listener()
    async def on_message(self, message):
        if not self.active:
            return
        if message.channel.id != self.channel_id:
            return
        if message.author.bot:
            return

        content = message.content.strip().lower()
        words = content.split()
        if len(words) != 1:
            await message.delete()
            embed = discord.Embed(
                description=f"❌ Je mag maar één woord typen! Beurt voorbij.",
                color=0x9b59b6
            )
            await message.channel.send(embed=embed)
            self.last_user_id = message.author.id
            return

        if self.last_user_id == message.author.id:
            embed = discord.Embed(
                description="❌ Je kan niet twee keer achter elkaar spelen!",
                color=0x9b59b6
            )
            await message.channel.send(embed=embed)
            return

        if self.last_word:
            if not content.startswith(self.last_word[-1]):
                embed = discord.Embed(
                    description=(
                        f"❌ Fout woord! Het moest beginnen met `{self.last_word[-1]}`.\n"
                        "Score is gereset. Nieuw spel begint!"
                    ),
                    color=0x9b59b6
                )
                await message.channel.send(embed=embed)
                if self.current_score > self.high_score:
                    self.high_score = self.current_score
                self.current_score = 0
                self.last_word = None
                self.last_user_id = None
                return

        self.current_score += 1
        self.last_word = content
        self.last_user_id = message.author.id

        embed = discord.Embed(
            description=f"✅ {message.author.display_name} heeft het woord `{content}` getypt!\n"
                        f"Huidige score: {self.current_score}",
            color=0x9b59b6
        )
        await message.channel.send(embed=embed)

        if self.current_score >= self.goal_points:
            embed = discord.Embed(
                description=f"🎉 Doel bereikt! Score: {self.current_score}",
                color=0x9b59b6
            )
            await message.channel.send(embed=embed)
            if self.current_score > self.high_score:
                self.high_score = self.current_score
            self.active = False
            self.current_score = 0
            self.last_word = None
            self.last_user_id = None
