import discord
from redbot.core import commands

class Woordspel(commands.Cog):
    """Een woordketting spel voor Discord met scoretracking."""

    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.channel_id = None
        self.current_score = 0
        self.high_score = 0
        self.last_word = None
        self.last_user_id = None
        self.goal_points = 10

    # ---------- Commands ----------

    @commands.command()
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
        await ctx.send(embed=self.make_embed(
            title="🎮 Woordspel gestart!",
            description=(
                f"Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n"
                f"Doel: {self.goal_points} punten\n\n"
                "Het spel begint nu! Typ je eerste woord."
            )
        ))

    @commands.command()
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

    @commands.command()
    async def totaal(self, ctx):
        """Toon de huidige score."""
        await ctx.send(f"Huidige score: {self.current_score}")

    @commands.command()
    async def highscore(self, ctx):
        """Toon de hoogste behaalde score."""
        await ctx.send(f"Hoogste score ooit: {self.high_score}")

    # ---------- Listener ----------

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.active or message.author.bot:
            return
        if message.channel.id != self.channel_id:
            return

        content = message.content.strip().lower()
        words = content.split()

        # Check op meerdere woorden
        if len(words) != 1:
            await message.delete()
            await message.channel.send(embed=self.make_embed(
                description=f"❌ Je mag maar één woord typen! Beurt voorbij."
            ))
            self.last_user_id = message.author.id
            return

        # Check op beurt
        if self.last_user_id == message.author.id:
            await message.channel.send(embed=self.make_embed(
                description="❌ Je kan niet twee keer achter elkaar spelen!"
            ))
            return

        # Check juiste beginletter
        if self.last_word:
            if not content.startswith(self.last_word[-1]):
                await message.channel.send(embed=self.make_embed(
                    description=(
                        f"❌ Fout woord! Het moest beginnen met `{self.last_word[-1]}`.\n"
                        "Score is gereset. Nieuw spel begint!"
                    )
                ))
                if self.current_score > self.high_score:
                    self.high_score = self.current_score
                self.current_score = 0
                self.last_word = None
                self.last_user_id = None
                return

        # Correct woord
        self.current_score += 1
        self.last_word = content
        self.last_user_id = message.author.id

        await message.channel.send(embed=self.make_embed(
            description=f"✅ {message.author.display_name} heeft het woord `{content}` getypt!\n"
                        f"Huidige score: {self.current_score}"
        ))

        # Check doelpunten
        if self.current_score >= self.goal_points:
            await message.channel.send(embed=self.make_embed(
                description=f"🎉 Doel bereikt! Score: {self.current_score}"
            ))
            if self.current_score > self.high_score:
                self.high_score = self.current_score
            self.active = False
            self.current_score = 0
            self.last_word = None
            self.last_user_id = None

    # ---------- Helper ----------

    def make_embed(self, title=None, description=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x9b59b6
        )
        return embed
