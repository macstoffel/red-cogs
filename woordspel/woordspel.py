import discord
from redbot.core import commands
import enchant  # extra dependency voor woordcontrole
from typing import Optional

class Woordspel(commands.Cog):
    """Een woordketting spel voor Discord met scoretracking en Nederlandse woordcontrole.
    Ondersteunt meerdere guilds tegelijk (per-guild game state)."""

    def __init__(self, bot):
        self.bot = bot
        # Per-guild spelstatus
        # structuur per guild_id:
        # {
        #   "active": bool,
        #   "channel_id": int,
        #   "current_score": int,
        #   "high_score": int,
        #   "last_word": Optional[str],
        #   "last_user_id": Optional[int],
        #   "goal_points": int
        # }
        self.games = {}

        # Nederlandse woordenlijst (gedeeld)
        try:
            self.nl_dict = enchant.Dict("nl_NL")
        except enchant.errors.DictNotFoundError:
            self.nl_dict = None

    # ---------- helpers ----------
    def _get_state(self, guild_id: int) -> dict:
        st = self.games.setdefault(guild_id, {
            "active": False,
            "channel_id": None,
            "current_score": 0,
            "high_score": 0,
            "last_word": None,
            "last_user_id": None,
            "goal_points": 10
        })
        return st

    # -------------------- Hoofdcommand groep --------------------
    @commands.group()
    async def woordspel(self, ctx):
        """Hoofdcommand voor het Woordspel."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # -------------------- Subcommands --------------------
    @woordspel.command()
    async def start(self, ctx, goal: int = 10):
        """Start het woordspel (per guild)."""
        if self.nl_dict is None:
            await ctx.send("⚠️ Nederlandse woordenlijst niet gevonden. Installeer pyenchant met Nederlandse dictionaries.")
            return

        st = self._get_state(ctx.guild.id)
        if st["active"]:
            await ctx.send("Er is al een spel actief in deze server!")
            return

        st["active"] = True
        st["channel_id"] = ctx.channel.id
        st["current_score"] = 0
        st["last_word"] = None
        st["last_user_id"] = None
        st["goal_points"] = goal

        await ctx.send(embed=self.make_embed(
            title="🎮 Woordspel gestart!",
            description=(
                f"Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n"
                f"Doel: {st['goal_points']} punten\n\n"
                "Het spel begint nu! Typ je eerste woord."
            )
        ))

    @woordspel.command()
    async def stop(self, ctx):
        """Stop het woordspel (per guild)."""
        st = self._get_state(ctx.guild.id)
        if not st["active"]:
            await ctx.send("Er is geen actief spel in deze server!")
            return
        st["active"] = False
        st["current_score"] = 0
        st["last_word"] = None
        st["last_user_id"] = None
        await ctx.send("Het woordspel is gestopt.")

    @woordspel.command()
    async def totaal(self, ctx):
        """Toon de huidige score (per guild)."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(f"Huidige score: {st['current_score']}")

    @woordspel.command()
    async def highscore(self, ctx):
        """Toon de hoogste behaalde score (per guild)."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(f"Hoogste score ooit: {st['high_score']}")

    @woordspel.command()
    async def help(self, ctx):
        """Toon een overzicht van alle subcommands."""
        embed = self.make_embed(
            title="Woordspel Commands",
            description=(
                "`[p]woordspel start [doelpunten]` - Start het spel (doelpunten optioneel)\n"
                "`[p]woordspel stop` - Stop het spel\n"
                "`[p]woordspel totaal` - Toon huidige score\n"
                "`[p]woordspel highscore` - Toon hoogste score ooit\n"
                "`[p]woordspel help` - Toon dit overzicht"
            )
        )
        await ctx.send(embed=embed)

    # -------------------- Listener --------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        # ignore bots / DMs
        if message.author.bot or not message.guild:
            return

        st = self._get_state(message.guild.id)
        if not st["active"]:
            return
        if message.channel.id != st["channel_id"]:
            return

        content = message.content.strip().lower()
        words = content.split()

        # Check op meerdere woorden
        if len(words) != 1:
            try:
                await message.delete()
            except Exception:
                pass
            st["last_user_id"] = message.author.id
            await message.channel.send(embed=self.make_embed(
                description=f"❌ Je mag maar één woord typen! Beurt voorbij."
            ))
            return

        # Check beurt (niet twee keer achter elkaar)
        if st["last_user_id"] == message.author.id:
            await message.channel.send(embed=self.make_embed(
                description="❌ Je kan niet twee keer achter elkaar spelen!"
            ))
            return

        # Check juiste beginletter (als er een last_word is)
        if st["last_word"]:
            required = st["last_word"][-1]
            if not content.startswith(required):
                # fout begonnen met verkeerde letter -> reset / herstart spel met uitleg
                if st["current_score"] > st["high_score"]:
                    st["high_score"] = st["current_score"]
                st["current_score"] = 0
                st["last_word"] = None
                st["last_user_id"] = None
                st["active"] = True  # start nieuw spel direct
                await message.channel.send(embed=self.make_embed(
                    title="🔁 Fout beginletter — Nieuw spel gestart!",
                    description=(
                        f"❌ Het woord moest beginnen met `{required}` maar `{content}` begint anders.\n\n"
                        "Het spel is opnieuw gestart en de score is gereset.\n\n"
                        "Regels:\n"
                        "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                        "- Je mag niet twee keer achter elkaar.\n"
                        "- Typ geen meerdere woorden tegelijk!\n\n"
                        "Typ je eerste woord om te beginnen."
                    )
                ))
                return

        # Check of het woord bestaat
        if not self.nl_dict.check(content):
            # ongeldig woord -> reset / herstart spel met uitleg
            st["last_user_id"] = message.author.id
            if st["current_score"] > st["high_score"]:
                st["high_score"] = st["current_score"]
            st["current_score"] = 0
            st["last_word"] = None
            st["last_user_id"] = None
            st["active"] = True  # start nieuw spel direct
            await message.channel.send(embed=self.make_embed(
                title="🔁 Ongeldig woord — Nieuw spel gestart!",
                description=(
                    f"❌ `{content}` is geen geldig Nederlands woord! De score is gereset.\n\n"
                    "Het spel is opnieuw gestart.\n\n"
                    "Regels:\n"
                    "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                    "- Je mag niet twee keer achter elkaar.\n"
                    "- Typ geen meerdere woorden tegelijk!\n\n"
                    "Typ je eerste woord om te beginnen."
                )
            ))
            return

        # Correct woord
        st["current_score"] += 1
        st["last_word"] = content
        st["last_user_id"] = message.author.id

        await message.channel.send(embed=self.make_embed(
            description=f"✅ {message.author.display_name} heeft het woord `{content}` getypt!\nStart het volgende woord met de laatste letter\n"
                        f"Huidige score: {st['current_score']}\nDoel: {st['goal_points']}"
        ))

        # Check doelpunten
        if st["current_score"] >= st["goal_points"]:
            await message.channel.send(embed=self.make_embed(
                description=f"🎉 Doel bereikt! Score: {st['current_score']}"
            ))
            if st["current_score"] > st["high_score"]:
                st["high_score"] = st["current_score"]
            st["active"] = False
            st["current_score"] = 0
            st["last_word"] = None
            st["last_user_id"] = None

    # -------------------- Helper --------------------
    def make_embed(self, title=None, description=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x9b59b6
        )
        return embed
