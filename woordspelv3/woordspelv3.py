# woordspelv3.py
from email.mime import message
from turtle import st

import discord
from redbot.core import commands
import enchant
import asyncio
import json
import random
from typing import Optional
from pathlib import Path

BASE = Path(__file__).parent
DATA_FOLDER = BASE / "data"
DATA_FILE = DATA_FOLDER / "tasks.json"

DATA_FOLDER.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump({"guilds": {}}, f, ensure_ascii=False, indent=4)

EMBED_COLOR = 0x9b59b6
DEFAULT_TIMEOUT = 300


class WoordSpelV3(commands.Cog):
    """WoordspelV3 — woordketting met taken, persistent scores en extra opties."""

    def __init__(self, bot):
        self.bot = bot
        self.games = {}

        try:
            self.nl_dict = enchant.Dict("nl_NL")
        except Exception:
            self.nl_dict = None

        self.data_file: Path = DATA_FILE
        self.data = {}
        self._load_data()

        # laad persistent state in runtime
        for gid, gd in self.data.get("guilds", {}).items():
            saved = gd.get("saved_state", {})
            st = self.games.setdefault(int(gid), {})
            st.update({
                "active": False,
                "paused": False,
                "channel_id": None,
                "current_score": saved.get("current_score", 0),
                "high_score": saved.get("high_score", 0),
                "last_word": saved.get("last_word"),
                "last_user_id": saved.get("last_user_id"),
                "goal_points": saved.get("goal_points", 10),
                "pending_task": None
            })

    # -------------------- Persistent data helpers --------------------
    def _load_data(self):
        if not self.data_file.exists():
            self.data = {"guilds": {}}
            self._save_data()
            return
        try:
            text = self.data_file.read_text(encoding="utf-8")
            loaded = json.loads(text) if text else {}
            if not isinstance(loaded, dict):
                loaded = {}
            if "guilds" not in loaded or not isinstance(loaded["guilds"], dict):
                loaded["guilds"] = {}
            self.data = loaded
        except Exception:
            self.data = {"guilds": {}}
            self._save_data()

    def _save_data(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self.data_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[WoordSpelV3] Kon data niet opslaan: {e}")

    def _save_state(self, guild_id: int):
        st = self._get_state(guild_id)
        gd = self._get_guild_data(guild_id)
        gd["saved_state"] = {
            "current_score": st["current_score"],
            "high_score": st["high_score"],
            "last_word": st["last_word"],
            "last_user_id": st["last_user_id"],
            "goal_points": st["goal_points"]
        }
        self._save_data()

    def _get_guild_data(self, guild_id: int) -> dict:
        if "guilds" not in self.data:
            self.data["guilds"] = {}
        gid = str(guild_id)
        gd = self.data["guilds"].setdefault(gid, {
            "task_channel_id": None,
            "timeout_seconds": DEFAULT_TIMEOUT,
            "tasks": [
                "Typ 'klaar' om verder te gaan",
                "Typ een woord van 6 letters",
                "Stuur een emoji",
                "Vertel een korte mop",
                "Typ het alfabet achterstevoren"
            ],
            "keep_score_on_task_success": False,
            "saved_state": {
                "current_score": 0,
                "high_score": 0,
                "last_word": None,
                "last_user_id": None,
                "goal_points": 10
            }
        })
        return gd

    # -------------------- Runtime state --------------------
    def _get_state(self, guild_id: int) -> dict:
        st = self.games.setdefault(guild_id, {
            "active": False,
            "channel_id": None,
            "current_score": 0,
            "high_score": 0,
            "last_word": None,
            "last_user_id": None,
            "goal_points": 10,
            "paused": False,
            "pending_task": None
        })
        return st

    # -------------------- Helper embed --------------------
    def make_embed(self, title: Optional[str] = None, description: Optional[str] = None):
        return discord.Embed(title=title, description=description, color=EMBED_COLOR)

    # -------------------- Commands --------------------
    @commands.group(name="ws3", invoke_without_command=True)
    async def ws(self, ctx):
        await ctx.send(embed=self.make_embed(
            title="Woordspel V3",
            description="Gebruik `$ws help` voor alle commands."
        ))

    @ws.command(name="start")
    async def start(self, ctx, goal: int = 10):
        if self.nl_dict is None:
            await ctx.send(embed=self.make_embed(
                title="⚠️ Dictionary niet geladen",
                description="De Nederlandse dictionary van pyenchant is niet beschikbaar."
            ))
            return

        st = self._get_state(ctx.guild.id)
        st.update({
            "active": True,
            "paused": False,
            "channel_id": ctx.channel.id,
            "current_score": st["current_score"],
            "last_word": st["last_word"],
            "last_user_id": None,
            "goal_points": goal,
            "pending_task": None
        })

        self._save_state(ctx.guild.id)

        await ctx.send(embed=self.make_embed(
            title="🎮 Woordspel V3 gestart!",
            description=f"Doel: {goal} punten\nTyp je eerste woord."
        ))

    @ws.command(name="stop")
    async def stop(self, ctx):
        st = self._get_state(ctx.guild.id)
        st.update({
            "active": False,
            "paused": False,
            "pending_task": None
        })
        self._save_state(ctx.guild.id)

        await ctx.send(embed=self.make_embed(
            title="🛑 Spel gestopt",
            description="Het spel is gestopt."
        ))

    @ws.command(name="totaal")
    async def totaal(self, ctx):
        st = self._get_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="Huidige score",
            description=f"Score: {st['current_score']}"
        ))

    @ws.command(name="highscore")
    async def highscore(self, ctx):
        st = self._get_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="Highscore",
            description=f"Highscore: {st['high_score']}"
        ))

    # -------------------- Nieuwe admin commands --------------------
    @ws.command(name="setscore")
    @commands.mod_or_permissions(manage_guild=True)
    async def setscore(self, ctx, score: int):
        st = self._get_state(ctx.guild.id)
        st["current_score"] = max(0, score)
        self._save_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="🔧 Score aangepast",
            description=f"Score is nu {score}"
        ))

    @ws.command(name="sethighscore")
    @commands.mod_or_permissions(manage_guild=True)
    async def sethighscore(self, ctx, score: int):
        st = self._get_state(ctx.guild.id)
        st["high_score"] = max(0, score)
        self._save_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="🏆 Highscore aangepast",
            description=f"Highscore is nu {score}"
        ))

    @ws.command(name="keepscore")
    @commands.mod_or_permissions(manage_guild=True)
    async def keepscore(self, ctx, waarde: bool):
        gd = self._get_guild_data(ctx.guild.id)
        gd["keep_score_on_task_success"] = waarde
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="⚙️ Instelling aangepast",
            description=f"Score behouden bij taak-succes staat nu op **{waarde}**"
        ))

    # -------------------- Takenbeheer --------------------
    @ws.command(name="taakadd")
    @commands.mod_or_permissions(manage_guild=True)
    async def taakadd(self, ctx, *, tekst: str):
        gd = self._get_guild_data(ctx.guild.id)
        gd["tasks"].append(tekst)
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="Taak toegevoegd",
            description=f"ID {len(gd['tasks']) - 1}: {tekst}"
        ))

    @ws.command(name="taakremove")
    @commands.mod_or_permissions(manage_guild=True)
    async def taakremove(self, ctx, taak_id: int):
        gd = self._get_guild_data(ctx.guild.id)
        if 0 <= taak_id < len(gd["tasks"]):
            removed = gd["tasks"].pop(taak_id)
            self._save_data()
            await ctx.send(embed=self.make_embed(
                title="Taak verwijderd",
                description=f"Verwijderd: {removed}"
            ))
        else:
            await ctx.send(embed=self.make_embed(description="❌ Ongeldig ID."))

    @ws.command(name="taken")
    async def taken(self, ctx):
        gd = self._get_guild_data(ctx.guild.id)
        if not gd["tasks"]:
            await ctx.send(embed=self.make_embed(title="Takenlijst", description="Geen taken."))
            return
        desc = "\n".join(f"**{i}** — {t}" for i, t in enumerate(gd["tasks"]))
        await ctx.send(embed=self.make_embed(title="Takenlijst", description=desc))

    @ws.command(name="taskchannel")
    @commands.mod_or_permissions(manage_guild=True)
    async def taskchannel(self, ctx, channel: Optional[discord.TextChannel] = None):
        if channel is None:
            channel = ctx.channel
        gd = self._get_guild_data(ctx.guild.id)
        gd["task_channel_id"] = channel.id
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="Taak-kanaal ingesteld",
            description=f"Taken worden nu gepost in {channel.mention}"
        ))

    @ws.command(name="timeout")
    @commands.mod_or_permissions(manage_guild=True)
    async def timeout(self, ctx, seconds: int):
        if seconds <= 0:
            await ctx.send(embed=self.make_embed(description="❌ Timeout moet > 0 zijn."))
            return
        gd = self._get_guild_data(ctx.guild.id)
        gd["timeout_seconds"] = seconds
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="Timeout aangepast",
            description=f"Timeout is nu {seconds} seconden."
        ))

    # -------------------- Message listener --------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        try:
            ctx = await self.bot.get_context(message)
            if ctx and ctx.command:
                return
        except Exception:
            pass

        st = self._get_state(message.guild.id)
        gd = self._get_guild_data(message.guild.id)

        # Task channel
        if gd.get("task_channel_id") and message.channel.id == gd["task_channel_id"]:
            pending = st.get("pending_task")
            if pending and pending.get("user_id") == message.author.id and st.get("paused"):
                th = pending.get("timeout_handle")
                if th and not th.done():
                    th.cancel()

                st["paused"] = False
                st["pending_task"] = None
                self._save_state(message.guild.id)

                game_ch = message.guild.get_channel(st["channel_id"])
                await message.channel.send(embed=self.make_embed(
                    title="Taak voltooid",
                    description=f"{message.author.mention} heeft de taak voltooid!"
                ))
                if game_ch:
                    await game_ch.send(embed=self.make_embed(
                        title="Spel hervat",
                        description=f"Laatste woord: `{st['last_word']}`"
                    ))
            return

        if not st["active"] or message.channel.id != st["channel_id"]:
            return

        if st.get("paused"):
            await message.channel.send(embed=self.make_embed(
                description="🛑 Spel gepauzeerd — voer eerst de taak uit."
            ))
            return

        content = message.content.strip().lower()
        words = content.split()

        if len(words) != 1:
            await message.delete()
            return

        if st["last_user_id"] == message.author.id:
            await message.channel.send(embed=self.make_embed(
                description="❌ Je mag niet twee keer achter elkaar!"
            ))
            return

        if st["last_word"]:
            required = st["last_word"][-1]
            if not content.startswith(required):
                await self._assign_task_for_incorrect(
                    message.guild, message.author, message.channel,
                    f"Het woord moest beginnen met `{required}`.",
                    st["last_word"]
                )
                return

        if not self.nl_dict.check(content):
            await self._assign_task_for_incorrect(
                message.guild, message.author, message.channel,
                f"`{content}` is geen geldig Nederlands woord!",
                st["last_word"]
            )
            return

        # correct woord
        st["current_score"] += 1
        st["last_word"] = content
        st["last_user_id"] = message.author.id
        self._save_state(message.guild.id)

        last_letter = content[-1]

        await message.channel.send(embed=self.make_embed(
            title="Correct woord!",
            description=(
                f"✅ `{content}` is correct!\n\n"
                f"➡️ Volgend woord moet beginnen met: **`{last_letter}`**\n\n"
                f"📊 Huidige score: **{st['current_score']}**\n"
                f"🎯 Doel: **{st['goal_points']}**"
                )
        ))

        if st["current_score"] >= st["goal_points"]:
            await message.channel.send(embed=self.make_embed(
                description=f"🎉 Doel bereikt! Score: {st['current_score']}"
            ))
            if st["current_score"] > st["high_score"]:
                st["high_score"] = st["current_score"]
            st.update({
                "active": False,
                "current_score": 0,
                "last_word": None,
                "last_user_id": None
            })
            self._save_state(message.guild.id)

    # -------------------- Task assignment --------------------
    async def _assign_task_for_incorrect(self, guild, user, game_channel, reason_text, previous_last_word):
        st = self._get_state(guild.id)
        gd = self._get_guild_data(guild.id)

        if not gd.get("keep_score_on_task_success", False):
            st["current_score"] = 0

        if st["current_score"] > st["high_score"]:
            st["high_score"] = st["current_score"]

        st["paused"] = True
        st["pending_task"] = {
            "user_id": user.id,
            "task_text": random.choice(gd["tasks"]) if gd["tasks"] else "Typ een bericht om verder te gaan.",
            "assigned_at": asyncio.get_event_loop().time()
        }
        st["last_word"] = previous_last_word
        st["last_user_id"] = user.id
        self._save_state(guild.id)

        await game_channel.send(embed=self.make_embed(
            title="🛑 Fout woord — Spel gepauzeerd",
            description=f"{user.mention}: {reason_text}\nVoer de taak uit in het taak-kanaal."
        ))

        task_ch = guild.get_channel(gd.get("task_channel_id"))
        if task_ch:
            await task_ch.send(embed=self.make_embed(
                title="📝 Taak toegewezen",
                description=f"{user.mention}, taak:\n> {st['pending_task']['task_text']}"
            ))

        timeout_seconds = gd.get("timeout_seconds", DEFAULT_TIMEOUT)
        th = asyncio.create_task(self._task_timeout_handler(guild.id, timeout_seconds))
        st["pending_task"]["timeout_handle"] = th

    async def _task_timeout_handler(self, guild_id: int, timeout_seconds: int):
        try:
            await asyncio.sleep(timeout_seconds)
            st = self._get_state(guild_id)
            if not st.get("paused") or not st.get("pending_task"):
                return

            user_id = st["pending_task"]["user_id"]
            st["paused"] = False
            st["pending_task"] = None
            self._save_state(guild_id)

            guild = self.bot.get_guild(guild_id)
            gd = self._get_guild_data(guild_id)

            game_ch = guild.get_channel(st["channel_id"])
            task_ch = guild.get_channel(gd.get("task_channel_id"))

            if task_ch:
                await task_ch.send(embed=self.make_embed(
                    title="⏱️ Taak verlopen",
                    description=f"<@{user_id}> heeft de taak niet uitgevoerd."
                ))
            if game_ch:
                await game_ch.send(embed=self.make_embed(
                    title="▶️ Spel hervat",
                    description=f"Laatste woord: `{st['last_word']}`"
                ))

        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[WoordSpelV3] Error in timeout handler: {e}")
