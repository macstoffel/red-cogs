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

    # Per-guild helper: check whether reused words are allowed (default: False = reuse not allowed)
    def _allow_reuse(self, guild_id: int) -> bool:
        return bool(self.settings.get(str(guild_id), {}).get("allow_reuse", False))

    @checks.mod_or_permissions(administrator=True)
    @commands.command(name="setreuse")
    async def setreuse(self, ctx, allow: Optional[str] = None):
        """Schakel het gebruik van eerder gebruikte woorden in/uit per guild.
        Gebruik true/false (of yes/no/on/off/1/0). Zonder argument toont de huidige instelling."""
        gid = str(ctx.guild.id)
        cfg = self.settings.get(gid, {})

        if allow is None:
            current = bool(cfg.get("allow_reuse", False))
            return await ctx.send(embed=self.make_embed(
                description=f"🔁 Huidige instelling: hergebruik is **{'ingeschakeld' if current else 'uitgeschakeld'}**."
            ))

        val = allow.strip().lower()
        if val in ("true", "1", "yes", "y", "on"):
            enabled = True
        elif val in ("false", "0", "no", "n", "off"):
            enabled = False
        else:
            return await ctx.send(embed=self.make_embed(
                description="❌ Ongeldige waarde. Gebruik `true` of `false` (of yes/no/on/off/1/0)."
            ))

        cfg["allow_reuse"] = enabled
        self.settings[gid] = cfg
        self._save_settings()
        await ctx.send(embed=self.make_embed(
            description=f"✅ Hergebruik van eerder gebruikte woorden is nu **{'ingeschakeld' if enabled else 'uitgeschakeld'}**."
        ))

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
            "cooldown": False,
            # extra: wie moet de taak uitvoeren en welke taak
            "task_assignee_id": None,
            "task_text": None
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
        st["task_assignee_id"] = None
        st["task_text"] = None

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
        st["task_assignee_id"] = None
        st["task_text"] = None
        await ctx.send(embed=self.make_embed(title="🟥 Woordspel_TD gestopt."))

    @woordspel_td.command()
    async def total(self, ctx):
        """Toon huidige score."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(description=f"Huidige score: {st['current_score']}"))

    @woordspel_td.command()
    async def myscore(self, ctx):
        """Toon persoonlijke score (leaderboard)."""
        score = self.leaderboard.get(str(ctx.author.id), 0)
        await ctx.send(embed=self.make_embed(description=f"📊 {ctx.author.display_name}, jouw score: {score}"))

    @woordspel_td.command()
    async def leaderboard(self, ctx):
        """Top 10 leaderboard."""
        sorted_lb = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
        msg = "**🏆 Leaderboard Top 10:**\n"
        for idx, (uid, score) in enumerate(sorted_lb, start=1):
            user = ctx.guild.get_member(int(uid))
            name = user.display_name if user else f"User {uid}"
            msg += f"{idx}. {name}: {score}\n"
        await ctx.send(embed=self.make_embed(description=msg))

    @woordspel_td.command()
    async def used(self, ctx, woord: str):
        """Bekijk wie een woord eerder gebruikte."""
        woord = woord.lower()
        used = self.words["used_words"].get(woord)
        if used:
            user = ctx.guild.get_member(used)
            if user:
                await ctx.send(embed=self.make_embed(description=f"📌 `{woord}` werd eerder gebruikt door **{user.display_name}**"))
            else:
                await ctx.send(embed=self.make_embed(description=f"📌 `{woord}` werd eerder gebruikt, gebruiker niet meer in server."))
        else:
            await ctx.send(embed=self.make_embed(description=f"`{woord}` is nog nooit gebruikt."))

    # -------------------- Taken --------------------
    @woordspel_td.command()
    async def task(self, ctx):
        """Geef een willekeurige taak."""
        if not self.tasks["tasks"]:
            await ctx.send(embed=self.make_embed(description="⚠️ Geen taken gevonden."))
            return
        taak = random.choice(self.tasks["tasks"])
        await ctx.send(embed=self.make_embed(description=f"🎯 Taak #{taak['id']}:\n{taak['text']}"))

    @checks.mod_or_permissions(administrator=True)
    @woordspel_td.command()
    async def settaskchannel(self, ctx, channel: discord.TextChannel):
        """Stel kanaal in waar taken uitgevoerd moeten worden."""
        self.settings[str(ctx.guild.id)] = {"task_channel": channel.id}
        self._save_settings()
        await ctx.send(embed=self.make_embed(description=f"✅ Taken-kanaal ingesteld op {channel.mention}"))

    @woordspel_td.command()
    async def addtask(self, ctx, *, tekst: str):
        """Voegt een taak toe met NSFW-veilige controle."""
        banned = ["porn", "penis", "vagina", "deepthroat", "real person", "naaktfoto"]
        lower = tekst.lower()
        for b in banned:
            if b in lower:
                await ctx.send(embed=self.make_embed(description="❌ Deze taak is te expliciet. Alleen suggestief/speels, geen echte personen."))
                return
        if "foto van je" in lower or "echte persoon" in lower or "naakt van jezelf" in lower:
            await ctx.send(embed=self.make_embed(description="❌ Geen echte personen toegestaan, enkel verhalen of speelgoed/voorwerpen."))
            return
        new_id = len(self.tasks["tasks"]) + 1
        self.tasks["tasks"].append({
            "id": new_id,
            "text": tekst,
            "added_by": str(ctx.author.id)
        })
        self._save_tasks()
        await ctx.send(embed=self.make_embed(description=f"✅ Taak toegevoegd (#{new_id})"))

    @woordspel_td.command()
    async def listtasks(self, ctx):
        if not self.tasks["tasks"]:
            await ctx.send(embed=self.make_embed(description="⚠️ Geen taken."))
            return
        msg = "**Takenlijst**\n"
        for t in self.tasks["tasks"]:
            msg += f"#{t['id']}: {t['text']}\n"
        await ctx.send(embed=self.make_embed(description=msg))

    # -------------------- Listener --------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        st = self._get_state(message.guild.id)
        if not st["active"]:
            return
        if message.channel.id != st["channel_id"]:
            return

        # If game is paused for a task, remove any attempts in game channel and notify briefly
        if st["cooldown"]:
            try:
                await message.delete()
            except Exception:
                pass
            assignee_id = st.get("task_assignee_id")
            assignee = message.guild.get_member(assignee_id) if assignee_id else None
            assignee_display = assignee.display_name if assignee else "een speler"
            notify = await message.channel.send(embed=self.make_embed(
                description=f"⏸️ Het spel is gepauzeerd: {assignee_display} moet eerst de toegewezen taak uitvoeren."
            ))
            # auto-delete notify after 5 seconds
            await asyncio.sleep(5)
            try:
                await notify.delete()
            except Exception:
                pass
            return

        content = message.content.lower().strip()
        words = content.split()
        if len(words) != 1:
            try:
                await message.delete()
            except:
                pass
            await message.channel.send(embed=self.make_embed(
                description=f"❌ Je mag maar één woord typen! Beurt voorbij."
            ))
            st["last_user_id"] = message.author.id
            return

        # niet twee keer achter elkaar
        if st["last_user_id"] == message.author.id:
            await message.channel.send(embed=self.make_embed(
                description="❌ Je kunt niet twee keer achter elkaar spelen!"
            ))
            return

        # juiste beginletter
        if st["last_word"]:
            required = st["last_word"][-1]
            if not content.startswith(required):
                await self._handle_wrong_word(message, st, required=required)
                return

        # check geldig woord
        if not self.nl_dict.check(content):
            await self._handle_wrong_word(message, st)
            return

        # check op eerder gebruikt woord
        used = self.words["used_words"].get(content)
        # respect per-guild setting: als hergebruik is toegestaan, skip de penalty/check
        if used and not self._allow_reuse(message.guild.id):
            user = message.guild.get_member(used)
            mention = user.display_name if user else "Onbekend"
            await message.channel.send(embed=self.make_embed(
                description=f"❗ `{content}` werd eerder gebruikt door **{mention}**"
            ))
            # geef taak
            await self._give_task(message, cause_word=content)
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

        await message.channel.send(embed=self.make_embed(
            description=f"✅ {message.author.display_name} heeft het woord `{content}` getypt!\nStart het volgende woord met de laatste letter\n"
                        f"Huidige score: {st['current_score']}\nDoel: {st['goal']}"
        ))

        # check doel
        if st["current_score"] >= st["goal"]:
            await message.channel.send(embed=self.make_embed(description="🎉 Doel bereikt! Spel stopt."))
            st["active"] = False

    # -------------------- Helper functies --------------------
    async def _handle_wrong_word(self, message, st, required: Optional[str] = None, penalty: bool = True):
        """Fout woord: strafpunt, pauze en geef taak. Start uitleg / reset as requested."""
        if penalty:
            st["current_score"] = max(0, st["current_score"] - 1)

        # store assignee for the task (the user who made mistake)
        st["task_assignee_id"] = message.author.id
        # keep last_word as-is so after task completes players know where to continue

        # notify in game channel and then give a task
        if required:
            title = "🔁 Fout beginletter — Spel gepauzeerd!"
            desc = (
                f"❌ Het woord moest beginnen met `{required}`, maar `{message.content}` begint anders.\n\n"
                f"Het spel is gepauzeerd en wacht op een taak van {message.author.display_name}.\n\n"
                "Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n\n"
                "De toegewezen taak moet uitgevoerd worden in het taak-kanaal."
            )
        else:
            title = "🔁 Ongeldig woord — Spel gepauzeerd!"
            desc = (
                f"❌ `{message.content}` is geen geldig Nederlands woord! De score is aangepast.\n\n"
                f"Het spel is gepauzeerd en wacht op een taak van {message.author.display_name}.\n\n"
                "Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n\n"
                "De toegewezen taak moet uitgevoerd worden in het taak-kanaal."
            )

        await message.channel.send(embed=self.make_embed(title=title, description=desc))
        await self._give_task(message, cause_word=message.content)

    async def _give_task(self, message, cause_word: Optional[str] = None):
        """Geef een taak aan de speler in het taak-kanaal."""
        st = self._get_state(message.guild.id)
        channel_id = self.settings.get(str(message.guild.id), {}).get("task_channel")
        if not channel_id:
            await message.channel.send(embed=self.make_embed(
                description="⚠️ Geen taak-kanaal ingesteld. Vraag een moderator om dit in te stellen."
            ))
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await message.channel.send(embed=self.make_embed(
                description="⚠️ Ongeldig taak-kanaal. Vraag een moderator om dit te herstellen."
            ))
            return

        assignee_id = st["task_assignee_id"]
        assignee = message.guild.get_member(assignee_id)

        # stuur taak in taak-kanaal
        try:
            await channel.send(embed=self.make_embed(
                title="🎯 Nieuwe taak toegewezen!",
                description=f"{assignee.display_name}, voer alsjeblieft de volgende taak uit:\n\n"
                            f"**{st['task_text']}**\n\n"
                            "Typ `klaar` als je de taak hebt voltooid."
            ))
        except Exception as e:
            await message.channel.send(embed=self.make_embed(
                description=f"⚠️ Kon geen taak verzenden in het taak-kanaal: {str(e)}"
            ))

        # pauzeer het spel totdat de taak is voltooid
        st["cooldown"] = True
        await message.channel.send(embed=self.make_embed(
            description=f"⏸️ Het spel is gepauzeerd. {assignee.display_name} moet de toegewezen taak uitvoeren."
        ))

        # wacht op taak voltooiing of timeout (bijv. 300 seconden)
        def check(m):
            return m.author == assignee and m.channel == channel and m.content.lower() == "klaar"

        try:
            await self.bot.wait_for("message", check=check, timeout=300.0)
            await channel.send(embed=self.make_embed(
                description=f"✅ Taak voltooid door {assignee.display_name}!"
            ))
            st["cooldown"] = False
            await message.channel.send(embed=self.make_embed(
                description="▶️ Het spel is hervat! Typ een nieuw woord."
            ))
        except asyncio.TimeoutError:
            await channel.send(embed=self.make_embed(
                description=f"⏰ Taak niet op tijd voltooid door {assignee.display_name}. Strafpunt toegekend."
            ))
            st["cooldown"] = False
            await message.channel.send(embed=self.make_embed(
                description="▶️ Het spel is hervat! Typ een nieuw woord."
            ))
        except Exception as e:
            await channel.send(embed=self.make_embed(
                description=f"⚠️ Fout bij het wachten op taak-voltooiing: {str(e)}"
            ))
            st["cooldown"] = False
            await message.channel.send(embed=self.make_embed(
                description="▶️ Het spel is hervat! Typ een nieuw woord."
            ))

    def make_embed(self, title: str = None, description: str = None, color: int = 0x3498db):
        """Maak een gestandaardiseerde embed voor berichten."""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Woordspel_TD | Versie 2.1")
        return embed
