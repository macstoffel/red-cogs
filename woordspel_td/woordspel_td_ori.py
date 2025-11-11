import discord
from redbot.core import commands, checks, Config
import enchant
import json
import os
import random
import asyncio
from typing import Optional

class WoordspelTD(commands.Cog):
    """Versie 2.1 — Woordketting met JSON opslag, taken, leaderboard, strafpunten en automatische cooldown."""

    def __init__(self, bot):
        self.bot = bot

        # data mappen en bestanden
        self.data_folder = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_folder, exist_ok=True)

        self.words_file = os.path.join(self.data_folder, "words.json")
        self.tasks_file = os.path.join(self.data_folder, "tasks.json")
        self.leaderboard_file = os.path.join(self.data_folder, "leaderboard.json")
        self.settings_file = os.path.join(self.data_folder, "settings.json")

        self._load_words()
        self._load_tasks()
        self._load_leaderboard()
        self._load_settings()

        # NL dictionary
        try:
            self.nl_dict = enchant.Dict("nl_NL")
        except enchant.errors.DictNotFoundError:
            self.nl_dict = None

        # per guild games
        self.games = {}

    # ---------- JSON LOAD / SAVE ----------
    def _load_words(self):
        if not os.path.exists(self.words_file):
            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump({"used_words": {}}, f, indent=4)
        with open(self.words_file, "r", encoding="utf-8") as f:
            self.words = json.load(f)

    def _save_words(self):
        with open(self.words_file, "w", encoding="utf-8") as f:
            json.dump(self.words, f, indent=4)

    def _load_tasks(self):
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump({"tasks": []}, f, indent=4)
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            self.tasks = json.load(f)

    def _save_tasks(self):
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=4)

    def _load_leaderboard(self):
        if not os.path.exists(self.leaderboard_file):
            with open(self.leaderboard_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
        with open(self.leaderboard_file, "r", encoding="utf-8") as f:
            self.leaderboard = json.load(f)

    def _save_leaderboard(self):
        with open(self.leaderboard_file, "w", encoding="utf-8") as f:
            json.dump(self.leaderboard, f, indent=4)

    def _load_settings(self):
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
        with open(self.settings_file, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

    def _save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    # ---------- spel state ----------
    def _get_state(self, guild_id: int) -> dict:
        return self.games.setdefault(guild_id, {
            "active": False,
            "channel_id": None,
            "current_score": 0,
            "high_score": 0,
            "last_word": None,
            "last_user_id": None,
            "goal": 10,
            "cooldown": False
        })

    # -------------------- Commands groep --------------------
    @commands.group()
    async def woordspel_td(self, ctx):
        """Hoofdcommand Woordspel_TD."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # -------------------- spel commands --------------------
    @woordspel_td.command()
    async def start(self, ctx, goal: int = 10):
        """Start het woordspel (per guild)."""
        if self.nl_dict is None:
            await ctx.send("⚠️ Nederlandse woordenlijst niet gevonden. Installeer pyenchant + NL dictionaries.")
            return

        st = self._get_state(ctx.guild.id)
        st["active"] = True
        st["channel_id"] = ctx.channel.id
        st["current_score"] = 0
        st["last_word"] = None
        st["last_user_id"] = None
        st["goal"] = goal
        st["cooldown"] = False

        await ctx.send(embed=self.make_embed(
            title="🎮 Woordspel_TD gestart!",
            description=f"Doel: {goal} punten.\nTyp je eerste woord!"
        ))

    @woordspel_td.command()
    async def stop(self, ctx):
        """Stop het spel."""
        st = self._get_state(ctx.guild.id)
        st["active"] = False
        st["current_score"] = 0
        st["last_word"] = None
        st["last_user_id"] = None
        st["cooldown"] = False
        await ctx.send("🟥 Woordspel_TD gestopt.")

    @woordspel_td.command()
    async def total(self, ctx):
        """Toon huidige score."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(f"Huidige score: {st['current_score']}")

    @woordspel_td.command()
    async def myscore(self, ctx):
        """Toon persoonlijke score (leaderboard)."""
        score = self.leaderboard.get(str(ctx.author.id), 0)
        await ctx.send(f"📊 {ctx.author.display_name}, jouw score: {score}")

    @woordspel_td.command()
    async def leaderboard(self, ctx):
        """Top 10 leaderboard."""
        sorted_lb = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "**🏆 Leaderboard Top 10:**\n"
        for idx, (uid, score) in enumerate(sorted_lb, start=1):
            user = ctx.guild.get_member(int(uid))
            name = user.display_name if user else f"User {uid}"
            msg += f"{idx}. {name}: {score}\n"
        await ctx.send(msg)

    @woordspel_td.command()
    async def used(self, ctx, woord: str):
        """Bekijk wie een woord eerder gebruikte."""
        woord = woord.lower()
        used = self.words["used_words"].get(woord)
        if used:
            user = ctx.guild.get_member(used)
            if user:
                await ctx.send(f"📌 `{woord}` werd eerder gebruikt door **{user.display_name}**")
            else:
                await ctx.send(f"📌 `{woord}` werd eerder gebruikt, gebruiker niet meer in server.")
        else:
            await ctx.send(f"`{woord}` is nog nooit gebruikt.")

    # -------------------- Taken --------------------
    @woordspel_td.command()
    async def task(self, ctx):
        """Geef een willekeurige taak."""
        if not self.tasks["tasks"]:
            await ctx.send("⚠️ Geen taken gevonden.")
            return
        taak = random.choice(self.tasks["tasks"])
        await ctx.send(f"🎯 Taak #{taak['id']}:\n{taak['text']}")

    @checks.mod_or_permissions(administrator=True)
    @woordspel_td.command()
    async def settaskchannel(self, ctx, channel: discord.TextChannel):
        """Stel kanaal in waar taken uitgevoerd moeten worden."""
        self.settings[str(ctx.guild.id)] = {"task_channel": channel.id}
        self._save_settings()
        await ctx.send(f"✅ Taken-kanaal ingesteld op {channel.mention}")

    @woordspel_td.command()
    async def addtask(self, ctx, *, tekst: str):
        """Voegt een taak toe met NSFW-veilige controle."""
        banned = ["porn", "penis", "vagina", "deepthroat", "real person", "naaktfoto"]
        lower = tekst.lower()
        for b in banned:
            if b in lower:
                await ctx.send("❌ Deze taak is te expliciet. Alleen suggestief/speels, geen echte personen.")
                return
        if "foto van je" in lower or "echte persoon" in lower or "naakt van jezelf" in lower:
            await ctx.send("❌ Geen echte personen toegestaan, enkel verhalen of speelgoed/voorwerpen.")
            return
        new_id = len(self.tasks["tasks"]) + 1
        self.tasks["tasks"].append({
            "id": new_id,
            "text": tekst,
            "added_by": str(ctx.author.id)
        })
        self._save_tasks()
        await ctx.send(f"✅ Taak toegevoegd (#%d)" % new_id)

    @woordspel_td.command()
    async def listtasks(self, ctx):
        if not self.tasks["tasks"]:
            await ctx.send("⚠️ Geen taken.")
            return
        msg = "**Takenlijst**\n"
        for t in self.tasks["tasks"]:
            msg += f"#{t['id']}: {t['text']}\n"
        await ctx.send(msg)

    # -------------------- Listener --------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        st = self._get_state(message.guild.id)
        if not st["active"] or st["cooldown"]:
            return
        if message.channel.id != st["channel_id"]:
            return

        content = message.content.lower().strip()
        words = content.split()
        if len(words) != 1:
            try:
                await message.delete()
            except:
                pass
            await message.channel.send(f"❌ Je mag maar één woord typen! Beurt voorbij.")
            st["last_user_id"] = message.author.id
            return

        # niet twee keer achter elkaar
        if st["last_user_id"] == message.author.id:
            await message.channel.send("❌ Je kunt niet twee keer achter elkaar spelen!")
            return

        # juiste beginletter
        if st["last_word"]:
            required = st["last_word"][-1]
            if not content.startswith(required):
                await self._handle_wrong_word(message, st, penalty=True)
                return

        # check geldig woord
        if not self.nl_dict.check(content):
            await self._handle_wrong_word(message, st, penalty=True)
            return

        # check op eerder gebruikt woord
        used = self.words["used_words"].get(content)
        if used:
            user = message.guild.get_member(used)
            mention = user.display_name if user else "Onbekend"
            await message.channel.send(f"❗ `{content}` werd eerder gebruikt door **{mention}**")
            # geef taak
            await self._give_task(message)
            return

        # Correct woord
        st["current_score"] += 1
        st["last_word"] = content
        st["last_user_id"] = message.author.id
        self.words["used_words"][content] = message.author.id
        self._save_words()

        # leaderboard update
        uid = str(message.author.id)
        self.leaderboard[uid] = self.leaderboard.get(uid, 0) + 1
        self._save_leaderboard()

        await message.channel.send(f"✅ `{content}` geaccepteerd! Score: {st['current_score']}")

        # check doel
        if st["current_score"] >= st["goal"]:
            await message.channel.send("🎉 Doel bereikt! Spel stopt.")
            st["active"] = False

    # -------------------- Helper functies --------------------
    async def _handle_wrong_word(self, message, st, penalty=False):
        """Fout woord: strafpunt, cooldown, nieuwe taak."""
        if penalty:
            st["current_score"] = max(0, st["current_score"] - 1)
        await message.channel.send(f"❌ Fout woord! Score -1. Huidige score: {st['current_score']}")
        await self._give_task(message)

    async def _give_task(self, message):
        """Geef een taak en pauzeer het spel totdat uitgevoerd."""
        st = self._get_state(message.guild.id)
        st["cooldown"] = True
        guild_id = str(message.guild.id)
        task_chan_id = self.settings.get(guild_id, {}).get("task_channel")
        if not task_chan_id:
            await message.channel.send("⚠️ Geen taak-kanaal ingesteld. Gebruik `[p]woordspel_td settaskchannel #kanaal`")
            st["cooldown"] = False
            return
        task_channel = message.guild.get_channel(task_chan_id)
        if not task_channel:
            await message.channel.send("⚠️ Taak-kanaal niet gevonden.")
            st["cooldown"] = False
            return
        if not self.tasks["tasks"]:
            await message.channel.send("⚠️ Geen taken beschikbaar.")
            st["cooldown"] = False
            return

        taak = random.choice(self.tasks["tasks"])
        await message.channel.send(f"🎯 {message.author.mention}, voer deze taak uit in {task_channel.mention}:\n{taak['text']}")

        def check(m):
            return m.author == message.author and m.channel.id == task_channel.id

        try:
            # wacht max 5 minuten op taak uitvoering
            await self.bot.wait_for("message", check=check, timeout=300)
            await message.channel.send(f"✅ Taak uitgevoerd! Spel gaat verder.")
        except asyncio.TimeoutError:
            await message.channel.send(f"❌ Taak niet uitgevoerd binnen 5 minuten. Spel gaat verder.")
        finally:
            st["cooldown"] = False

    def make_embed(self, title=None, description=None):
        embed = discord.Embed(title=title, description=description, color=0x9b59b6)
        return embed
