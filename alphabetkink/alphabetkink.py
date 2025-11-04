import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
import json
import os
from typing import Optional


class AlphabetKink(commands.Cog):
    """Kinky alfabet spel – A t/m Z met fetish/BDSM woorden + scores + JSON support"""

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
  "A": [
    "aftercare", "anal", "anaalplug", "anaaltrainers", "anaalkraal", "anaalketting",
    "afstraffing", "afknellen", "aambeeltring", "armpunten", "armbinder",
    "anatomicale fixatie", "ageplay", "animalplay", "abdomen-binding"
  ],
  "B": [
    "bondage", "buttplug", "ballgag", "boeien", "blinddoek", "benchwippen",
    "breathplay", "bitchslap", "bimboficatie", "bollenklem", "borstklem",
    "bruisballonplay", "brede spreidstang", "bodyharnas", "bondagezak",
    "bedfixatie", "ballstretcher", "bootworship", "butterfly-gag"
  ],
  "C": [
    "chastity", "collar", "consent", "cockring", "clamps", "caning", "choker",
    "candleplay", "cupping", "cageplay", "centrale fixatie", "corsettraining",
    "cross-collar bondage", "chastitybelt", "chainhogtie"
  ],
  "D": [
    "dom", "discipline", "dominant", "dogplay", "dwangbuis", "dildo", "deepthroat",
    "dasklemmen", "dungeon", "double-penetration-toys", "dovetail bondage",
    "disciplinestoel", "dwangkoord", "degradatiespel"
  ],
  "E": [
    "edgeplay", "electroplay", "erotiek", "exposure", "enema", "escortspel",
    "erotic spanking", "electrode cuffs", "electro-zadel", "elbowbinder",
    "extreme spreiding", "elastische bondage"
  ],
  "F": [
    "fetish", "fixatie", "flogger", "facesitting", "feetplay", "fisting",
    "fatale onderwerping", "faceharnas", "full-body mummificatie",
    "forced-orgasm", "forced-chastity", "footworship", "face-mask",
    "femdom", "forniphilia", "foam-gag", "foulard bondage"
  ],
  "G": [
    "gag", "gimp", "gagbal", "garotteplay", "gehoorzaamheid", "gasmaskerfetish",
    "gelreiniging (klysma)", "genitale fixatie", "gaiter restraints",
    "gooning", "g-stringplay", "gimpmask", "gigantische plug"
  ],
  "H": [
    "harnas", "handcuffs", "halsband", "hotwax", "humiliation",
    "hooggehangen benen", "hoodplay", "hogtie", "handspanking", "houten spreider",
    "hankleedstoel", "hondenpak (petplay)", "hypnoplay", "hanger bondage"
  ],
  "I": [
    "impactplay", "isoleerzak", "intieme slaaf", "inrijgkorset",
    "injectiespel (medisch kink)", "iceplay", "interrogationplay",
    "incontinentiespel (fetish)", "imperial gag", "iron collar"
  ],
  "J": [
    "jute", "jankballetje", "ja-meester-spel", "jurkenfetish", "jacket-restraints",
    "japanse touwkunst", "jerk-control", "joint-fixatie"
  ],
  "K": [
    "kinky", "kettingen", "kneveling", "kaarsvet", "kontslag", "kruisbank",
    "kuisheidsgordel", "kattenstaart", "kapfetish", "korsetdiscipline",
    "kniespreider", "kaakspreider", "kroepstok", "kousenfetish",
    "kietelmarteling", "kousenbinding"
  ],
  "L": [
    "latex", "leather", "leerfetish", "lingerieplay", "lijmfixatie",
    "leidsel", "latexmasker", "lijfketting", "linnenband bondage",
    "lijfobjectificatie", "latexhood", "lederen bitgag"
  ],
  "M": [
    "masochist", "master", "mascara-running", "maskerfetish", "mommy/daddyplay",
    "martelbank", "mummificatie", "medische kink", "metal bondage",
    "mouthhook", "monstermaskerbonds", "milking machine", "muiltijdband",
    "mantra-onderwerping", "metal cuffs", "massage-torture"
  ],
  "N": [
    "needleplay", "nippleclamps", "naaktbediening", "neglectplay", "neuzenring",
    "naald-torture", "nosing (petplay)", "nachtkraag", "narrow-hogtie"
  ],
  "O": [
    "opper", "o-ring", "overheersing", "onderwerping", "objectificatie",
    "oralservitude", "overtraining", "oorklemmen", "open-mouth gag",
    "overground hogtie", "ophijsbondage"
  ],
  "P": [
    "paddle", "petplay", "ponyplay", "pijnbank", "prikkelwiel", "peesfetish",
    "prostaatmassage", "pincette-clamps", "popharnas", "power-exchange",
    "puppygag", "positiecontrole", "public-humiliation", "piercingplay"
  ],
  "Q": [
    "queening", "queenstoel", "quick-release cuffs", "quickie-submission",
    "quad-spreider", "quiet-service (stilte kink)", "quiver-ropes"
  ],
  "R": [
    "ropes", "rigger", "rijzweep", "rattanstok", "roleplay (BDSM)",
    "ruw touw", "ropecuffs", "ringgag", "ropecorset", "riggingframe",
    "rode trap (discipline)", "ritssluiting-zipper", "rope-suspension",
    "rondhalsboei"
  ],
  "S": [
    "sub", "sadist", "spreaderbar", "slavin", "safeword", "shibari", "smplay",
    "sensorydeprivation", "spanking", "suspension", "strapon", "strap-corset",
    "suspensionframe", "suctioncups", "strappado", "siliconenboeien",
    "salivagag", "stilte-orde", "sissyficatie"
  ],
  "T": [
    "teasing", "tapeplay", "tietklemmen", "teugels", "touwbondage",
    "torture", "tweezers-clamps", "tittraining", "touwkorset",
    "tongklem", "toiletplay (mild en consensual kink)", "timeout-cage",
    "thighcuffs", "tens-unit play"
  ],
  "U": [
    "uniformplay", "uitkleden-op-commando", "urinering kink (mild consensual)",
    "uitbuiting-roleplay", "upperbody bondage", "underarm-binder",
    "unicorn-mask fetish", "unbreekbare discipline"
  ],
  "V": [
    "vettex", "vibrator", "vaginapomp", "voetenfetish", "voorover binden",
    "vuistklemmen", "vals-masker", "verhorenplay", "vleespak (latex)",
    "verplichte knielhouding", "voice-control", "vinegar-sting-wax"
  ],
  "W": [
    "whip", "waxplay", "wandelstok", "wartenbergwiel", "werkhond-spel",
    "wheel-of-pain", "wrists-to-ankles tie", "wipstoel", "wicked-rope",
    "waacking gag", "wrap-mummificatie"
  ],
  "X": [
    "x-frame", "xtreme-bondage", "x-positie", "x-cuffs", "x-harnas",
    "x-tied spreiding", "x-bench"
  ],
  "Y": [
    "yoke", "y-cuff", "y-vormige touwhouding", "y-positie hogtie",
    "yanker-clamps", "yarn-rope bondage"
  ],
  "Z": [
    "zipper", "zelfbinding", "zweep", "zwabberklemmen", "zenuwspel (electro)",
    "zwaar touwkorset", "zadelplay", "zwelplug", "zijden touw bondage"
  ]
}

        # JSON in cog data map
        self.words_file = cog_data_path(self) / "kink_words.json"

        # --- ✅ Belangrijk toegevoegd ---
        # Als JSON bestaat → laad hem
        # Als JSON NIET bestaat → schrijf standaard-woordenlijst naar JSON
        if os.path.exists(self.words_file):
            with open(self.words_file, "r", encoding="utf-8") as f:
                self.allowed_words = json.load(f)
        else:
            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump(self.allowed_words, f, indent=4, ensure_ascii=False)

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

        # ✅ sla op & vervang de woordenlijst
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
        """Overzicht met commands."""
        embed = await self.game_embed(
            "📌 Kink Alfabet Help",
            (
                "**$kinkalfabet** – Start/reset het spel\n"
                "**$kinksetchannel #kanaal** – Speelkanaal instellen\n"
                "**$kinkscore** – Bekijk je score\n"
                "**$kinktop** – Top 10 spelers\n"
                "**$kinkexport** – Exporteer woordenlijst\n"
                **"$kinkimport** – Importeer woordenlijst"
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

        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            await self.bot.process_commands(message)
            return

        game_channel = await self.config.game_channel()
        if not game_channel or message.channel.id != game_channel:
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
                "Geef andere spelers een beurt."
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

        # ✅ correct
        next_letter = "A" if current_letter == "Z" else chr(ord(current_letter) + 1)
        await self.config.current_letter.set(next_letter)
        await self.config.last_player.set(message.author.id)

        # score
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
