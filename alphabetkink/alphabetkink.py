import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
import json
import os
from typing import Optional


class AlphabetKink(commands.Cog):
    """Kinky alfabet spel voor Discord – A t/m Z met fetish/BDSM woorden"""

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=5566778899, force_registration=True)

        default_global = {
            "game_channel": None,
            "current_letter": "A",
            "last_player": None,
            "scores": {}
        }

        self.config.register_global(**default_global)

        # standaard woordenlijst
        self.allowed_words = {
            "A": ["aftercare", "anal"],
            "B": ["bondage", "buttplug", "ballgag"],
            "C": ["chastity", "collar", "consent"],
            "D": ["dom", "discipline", "dominant"],
            "E": ["edgeplay", "electroplay"],
            "F": ["fetish", "fixatie", "flogger"],
            "G": ["gag", "gimp"],
            "H": ["harnas", "handcuffs"],
            "I": ["impactplay"],
            "J": ["jute"],
            "K": ["kinky", "kettingen"],
            "L": ["latex", "leather"],
            "M": ["masochist", "master", "mascara-running"],
            "N": ["needleplay", "nippleclamps"],
            "O": ["opper", "o-ring"],
            "P": ["paddle", "petplay"],
            "Q": ["queening"],
            "R": ["ropes", "rigger"],
            "S": ["sub", "sadist", "spreaderbar"],
            "T": ["teasing", "tapeplay"],
            "U": ["uniformplay"],
            "V": ["vettex", "vibrator"],
            "W": ["whip", "waxplay"],
            "X": ["x-frame"],
            "Y": ["yoke"],
            "Z": ["zipper", "zelfbinding"],
        }

        # pad voor json
        self.words_file = cog_data_path(self) / "kink_words.json"

        # als er al een json opgeslagen is → laad die
        if os.path.exists(self.words_file):
            with open(self.words_file, "r", encoding="utf-8") as f:
                self.allowed_words = json.load(f)

    async def game_embed(self, title, desc, color=discord.Color.purple()):
        return discord.Embed(title=title, description=desc, color=color)

    # -------------------------
    # COMMANDS
    # -------------------------

    @commands.command()
    async def kinkalfabet(self, ctx):
        """Start of reset het kinky alfabet spel."""
        await self.config.current_letter.set("A")
        await self.config.last_player.set(None)

        embed = await self.game_embed(
            "Kinky Alfabet Spel gestart!",
            "Begin met een woord dat begint met **A**!"
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def kinksetchannel(self, ctx, channel: discord.TextChannel):
        """Stel het kanaal in waar het spel moet plaatsvinden."""
        await self.config.game_channel.set(channel.id)
        embed = await self.game_embed(
            "Kanaal ingesteld ✅",
            f"Het kinky alfabet spel wordt nu gespeeld in {channel.mention}."
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def kinkscore(self, ctx):
        """Bekijk je eigen score."""
        scores = await self.config.scores()
        score = scores.get(str(ctx.author.id), 0)

        embed = await self.game_embed(
            "📊 Jouw score",
            f"**{ctx.author.display_name}** heeft **{score}** punt(en)."
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def kinktop(self, ctx):
        """Top 10 spelers (meeste correcte woorden)."""
        scores = await self.config.scores()
        if not scores:
            return await ctx.send("Nog geen scores beschikbaar.")

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

        desc = ""
        for user_id, points in sorted_scores:
            user = ctx.guild.get_member(int(user_id))
            name = user.display_name if user else f"User {user_id}"
            desc += f"**{name}** – {points} punten\n"

        embed = await self.game_embed("🏆 Top 10 Kinky spelers", desc)
        await ctx.send(embed=embed)

    @commands.command()
    async def kinkexport(self, ctx):
        """Exporteer de huidige woordenlijst als JSON bestand."""
        with open(self.words_file, "w", encoding="utf-8") as f:
            json.dump(self.allowed_words, f, indent=4, ensure_ascii=False)

        await ctx.send(
            "✅ Woordenlijst geëxporteerd!",
            file=discord.File(self.words_file, filename="kink_words.json")
        )

    @commands.command()
    async def kinkimport(self, ctx):
        """
        Importeer een kinky woordenlijst uit een JSON bestand.
        Upload een .json en typ daarna: $kinkimport
        """
        if not ctx.message.attachments:
            return await ctx.send("❌ Je moet een JSON bestand uploaden.")

        attachment = ctx.message.attachments[0]

        if not attachment.filename.endswith(".json"):
            return await ctx.send("❌ Dat is geen .json bestand.")

        data = await attachment.read()
        try:
            new_list = json.loads(data)
        except json.JSONDecodeError:
            return await ctx.send("❌ Ongeldig JSON bestand!")

        if not isinstance(new_list, dict):
            return await ctx.send("❌ JSON moet een dict zijn: { 'A': ['anal', ...], ... }")

        # opslaan
        with open(self.words_file, "w", encoding="utf-8") as f:
            json.dump(new_list, f, indent=4, ensure_ascii=False)

        self.allowed_words = new_list

        embed = await self.game_embed(
            "✅ Woordenlijst geüpdatet!",
            "De nieuwe woordenlijst is succesvol geïmporteerd."
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def kinkhelp(self, ctx):
        """Overzicht van kinky alfabet commands."""
        embed = await self.game_embed(
            "📌 Kink Alfabet Help",
            (
                "**$kinkalfabet** – Start/reset het spel\n"
                "**$kinksetchannel #kanaal** – Stel speelkanaal in\n"
                "**$kinkscore** – Bekijk je score\n"
                "**$kinktop** – Top 10 spelers\n"
                "**$kinkexport** – Exporteer woordenlijst\n"
                "**$kinkimport** – Importeer woordenlijst\n"
            )
        )
        await ctx.send(embed=embed)

    # -------------------------
    # SPEL LOGICA
    # -------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # If this message is a command, let the bot process it and don't treat it as a game move.
        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            await self.bot.process_commands(message)
            return

        game_channel = await self.config.game_channel()
        if not game_channel or message.channel.id != game_channel:
            return

        prefix = tuple(await self.bot.get_prefix(message))
        if message.content.startswith(prefix):
            return

        word = message.content.lower().strip()
        if not word:
            return

        current_letter = await self.config.current_letter()
        last_player = await self.config.last_player()

        if word[0].upper() != current_letter:
            return

        if str(message.author.id) == str(last_player):
            embed = await self.game_embed(
                "❌ Je bent net geweest!",
                "Geef andere spelers ook een beurt."
            )
            return await message.channel.send(embed=embed)

        valid = self.allowed_words.get(current_letter, [])
        if word not in valid:
            await self.config.current_letter.set("A")
            await self.config.last_player.set(None)

            embed = await self.game_embed(
                "❌ Fout woord!",
                "Dat woord staat niet in de kinky lijst.\n🔁 Nieuw spel – begin met **A**"
            )
            return await message.channel.send(embed=embed)

        # ✅ correct woord
        next_letter = "A" if current_letter == "Z" else chr(ord(current_letter) + 1)
        await self.config.current_letter.set(next_letter)
        await self.config.last_player.set(message.author.id)

        # score opslaan
        scores = await self.config.scores()
        user_id = str(message.author.id)
        scores[user_id] = scores.get(user_id, 0) + 1
        await self.config.scores.set(scores)

        if current_letter == "Z":
            embed = await self.game_embed(
                "🎉 Z gehaald!",
                "Goed gedaan kinky mensen! 🔁 Nieuw spel – begin weer met **A**"
            )
        else:
            embed = await self.game_embed(
                "✅ Goed woord!",
                f"`{word}` is juist!\nVolgende letter: **{next_letter}**"
            )

        await message.channel.send(embed=embed)


async def setup(bot: Red):
    await bot.add_cog(AlphabetKink(bot))
