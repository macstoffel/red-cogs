# woordspelv2.py
import discord
from redbot.core import commands, data_manager
import enchant
import asyncio
import json
import random
from typing import Optional
from pathlib import Path

# Zorg dat er een schrijfbare data-map in de cog-map zelf is (vermijdt permission issues)
BASE = Path(__file__).parent
DATA_FOLDER = BASE / "data"
DATA_FILE = DATA_FOLDER / "tasks.json"

# aanmaken map (parents niet nodig hier omdat BASE al een map is) en file als die ontbreekt
DATA_FOLDER.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump({"tasks": []}, f, ensure_ascii=False, indent=4)

EMBED_COLOR = 0x9b59b6
DEFAULT_TIMEOUT = 300  # seconden (5 min)


class WoordSpelV2(commands.Cog):
    """WoordspelV2 — woordketting met taak-systeem, persisted data via Red-DiscordBot data_manager."""

    def __init__(self, bot):
        self.bot = bot

        # runtime state (niet persisted)
        # guild_id -> runtime dict
        self.games = {}

        # probeer NL dictionary
        try:
            self.nl_dict = enchant.Dict("nl_NL")
        except Exception:
            self.nl_dict = None

        # data file via Redbot data_manager
        # gebruik lokale cog-data file (schrijfbaar) als fallback / primaire opslag
        self.data_file: Path = DATA_FILE
        # bewaar ook container voor compatibility met eerdere code
        self.data = {}

        # laad of init persistent data
        self._load_data()

    # -------------------- Persistent data helpers --------------------
    def _load_data(self):
        if not self.data_file.exists():
            # default structure
            self.data = {"guilds": {}}
            self._save_data()
            return
        try:
            text = self.data_file.read_text(encoding="utf-8")
            self.data = json.loads(text) if text else {"guilds": {}}
        except Exception:
            # fallback safe default
            self.data = {"guilds": {}}
            self._save_data()

    def _save_data(self):
        try:
            self.data_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            # cannot raise here — log to console
            print(f"[WoordSpelV2] Kon data niet opslaan: {e}")

    def _get_guild_data(self, guild_id: int) -> dict:
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
            ]
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
            "pending_task": None  # dict: user_id, task_text, assigned_at, timeout_handle
        })
        return st

    # -------------------- Helper embed --------------------
    def make_embed(self, title: Optional[str] = None, description: Optional[str] = None):
        embed = discord.Embed(title=title, description=description, color=EMBED_COLOR)
        return embed

    # -------------------- Command group $ws --------------------
    @commands.group(name="ws", invoke_without_command=True)
    async def ws(self, ctx: commands.Context):
        """Woordspel V2 hoofdcommand — gebruik subcommands."""
        await ctx.send(embed=self.make_embed(
            title="Woordspel V2",
            description="Gebruik `$ws help` voor alle commands."
        ))

    # ---------- Basis commands ----------
    @ws.command(name="start")
    async def start(self, ctx: commands.Context, goal: int = 10):
        """Start het woordspel (per guild)."""
        if self.nl_dict is None:
            await ctx.send(embed=self.make_embed(
                title="⚠️ Dictionary niet geladen",
                description="De Nederlandse dictionary van pyenchant is niet beschikbaar."
            ))
            return

        st = self._get_state(ctx.guild.id)
        if st["active"] and not st["paused"]:
            await ctx.send(embed=self.make_embed(
                description="Er is al een actief spel in deze server!"
            ))
            return

        st.update({
            "active": True,
            "paused": False,
            "channel_id": ctx.channel.id,
            "current_score": 0,
            "last_word": None,
            "last_user_id": None,
            "goal_points": goal,
            "pending_task": None
        })

        await ctx.send(embed=self.make_embed(
            title="🎮 Woordspel V2 gestart!",
            description=(
                f"Regels:\n"
                "- Typ een woord dat begint met de laatste letter van het vorige woord.\n"
                "- Je mag niet twee keer achter elkaar.\n"
                "- Typ geen meerdere woorden tegelijk!\n\n"
                f"Doel: {st['goal_points']} punten\n\nHet spel begint nu! Typ je eerste woord."
            )
        ))

    @ws.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop het woordspel (per guild)."""
        st = self._get_state(ctx.guild.id)
        if not st["active"]:
            await ctx.send(embed=self.make_embed(description="Er is geen actief spel in deze server!"))
            return

        # cancel timeout if exists
        pending = st.get("pending_task")
        if pending and pending.get("timeout_handle"):
            th = pending["timeout_handle"]
            if not th.done():
                th.cancel()

        st.update({
            "active": False,
            "paused": False,
            "current_score": 0,
            "last_word": None,
            "last_user_id": None,
            "pending_task": None
        })

        await ctx.send(embed=self.make_embed(title="🛑 Spel gestopt", description="Het woordspel is gestopt."))

    @ws.command(name="totaal")
    async def totaal(self, ctx: commands.Context):
        """Toon de huidige score (per guild)."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="Huidige score",
            description=f"Huidige score: {st['current_score']}"
        ))

    @ws.command(name="highscore")
    async def highscore(self, ctx: commands.Context):
        """Toon de hoogste behaalde score (per guild)."""
        st = self._get_state(ctx.guild.id)
        await ctx.send(embed=self.make_embed(
            title="Hoogste score",
            description=f"Hoogste score ooit: {st['high_score']}"
        ))

    @ws.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        """Toon een overzicht van alle subcommands."""
        embed = self.make_embed(
            title="WoordspelV2 Commands ($ws ...)",
            description=(
                "`$ws start [doelpunten]` - Start het spel\n"
                "`$ws stop` - Stop het spel\n"
                "`$ws totaal` - Toon huidige score\n"
                "`$ws highscore` - Toon hoogste score\n"
                "`$ws taakadd <tekst>` - Voeg een taak toe (per guild)\n"
                "`$ws taakremove <id>` - Verwijder taak met id (per guild)\n"
                "`$ws taken` - Toont takenlijst (per guild)\n"
                "`$ws taskchannel #kanaal` - Stel taak-kanaal in\n"
                "`$ws timeout <seconden>` - Stel timeout in (default 300)\n"
                "\nWanneer iemand een fout woord typt, gaat het spel op pauze en krijgt die speler een taak in het taak-kanaal.\n"
                "Zodra de speler een bericht in het taak-kanaal plaatst, wordt het spel hervat."
            )
        )
        await ctx.send(embed=embed)

    # -------------------- Task management (persisted) --------------------
    @ws.command(name="taakadd")
    @commands.mod_or_permissions(manage_guild=True)
    async def taakadd(self, ctx: commands.Context, *, tekst: str):
        """Voeg een taak toe aan de guild-takenlijst (require manage_guild)."""
        gd = self._get_guild_data(ctx.guild.id)
        gd["tasks"].append(tekst)
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="✅ Taak toegevoegd",
            description=f"Taak ID {len(gd['tasks']) - 1}: {tekst}"
        ))

    @ws.command(name="taakremove")
    @commands.mod_or_permissions(manage_guild=True)
    async def taakremove(self, ctx: commands.Context, taak_id: int):
        """Verwijder taak op ID (require manage_guild)."""
        gd = self._get_guild_data(ctx.guild.id)
        if 0 <= taak_id < len(gd["tasks"]):
            removed = gd["tasks"].pop(taak_id)
            self._save_data()
            await ctx.send(embed=self.make_embed(
                title="🗑️ Taak verwijderd",
                description=f"Verwijderd (ID {taak_id}): {removed}"
            ))
        else:
            await ctx.send(embed=self.make_embed(
                description="❌ Ongeldig taak ID."
            ))

    @ws.command(name="taken")
    async def taken(self, ctx: commands.Context):
        """Toon alle taken (met ID) voor deze guild."""
        gd = self._get_guild_data(ctx.guild.id)
        if not gd["tasks"]:
            await ctx.send(embed=self.make_embed(title="Takenlijst", description="Geen taken ingesteld."))
            return
        desc_lines = []
        for i, t in enumerate(gd["tasks"]):
            short = t if len(t) < 150 else t[:147] + "..."
            desc_lines.append(f"**{i}** — {short}")
        await ctx.send(embed=self.make_embed(title="Takenlijst", description="\n".join(desc_lines)))

    @ws.command(name="taskchannel")
    @commands.mod_or_permissions(manage_guild=True)
    async def taskchannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Stel het taak-kanaal in voor deze guild. Gebruik `#kanaal` of laat leeg om huidig kanaal te gebruiken."""
        # fallback naar huidige channel wanneer geen argument gegeven
        if channel is None:
            channel = ctx.channel

        # controleer dat bot kan posten in het kanaal
        bot_member = ctx.guild.me or ctx.guild.get_member(self.bot.user.id)
        perms = channel.permissions_for(bot_member)
        if not perms.send_messages:
            return await ctx.send(embed=self.make_embed(
                description=f"❗ Ik kan niet posten in {channel.mention}. Controleer permissies voor de bot."
            ))

        gd = self._get_guild_data(ctx.guild.id)
        gd["task_channel_id"] = channel.id
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="✅ Taak-kanaal ingesteld",
            description=f"Taken zullen vanaf nu gepost worden in {channel.mention}"
        ))

    @ws.command(name="timeout")
    @commands.mod_or_permissions(manage_guild=True)
    async def timeout(self, ctx: commands.Context, seconds: int):
        """Stel de timeout (in seconden) in voor taken (per guild)."""
        if seconds <= 0:
            await ctx.send(embed=self.make_embed(description="❌ Timeout moet groter zijn dan 0."))
            return
        gd = self._get_guild_data(ctx.guild.id)
        gd["timeout_seconds"] = seconds
        self._save_data()
        await ctx.send(embed=self.make_embed(
            title="⏱️ Timeout aangepast",
            description=f"Timeout is nu {seconds} seconden."
        ))

    # -------------------- Message listener --------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore bots / DMs
        if message.author.bot or not message.guild:
            return

        st = self._get_state(message.guild.id)
        gd = self._get_guild_data(message.guild.id)

        # If message is in the task-channel, check for task completion
        task_channel_id = gd.get("task_channel_id")
        if task_channel_id and message.channel.id == task_channel_id:
            pending = st.get("pending_task")
            if pending and pending.get("user_id") == message.author.id and st.get("paused"):
                # cancel timeout handle
                th = pending.get("timeout_handle")
                if th and not th.done():
                    th.cancel()

                # clear pending task
                st["paused"] = False
                st["pending_task"] = None

                # notify both channels
                game_ch = message.guild.get_channel(st["channel_id"]) if st.get("channel_id") else None

                await message.channel.send(embed=self.make_embed(
                    title="✅ Taak voltooid",
                    description=(f"{message.author.mention} heeft de taak voltooid — het spel wordt hervat.\n\n"
                                 f"Laatste correcte woord: `{st['last_word'] or 'geen'}`")
                ))

                if game_ch:
                    await game_ch.send(embed=self.make_embed(
                        title="▶️ Spel hervat",
                        description=(f"{message.author.display_name} heeft de taak voltooid — het spel gaat verder.\n\n"
                                     f"Laatste correcte woord: `{st['last_word'] or 'geen'}`\n"
                                     f"Volgend woord moet beginnen met: `{(st['last_word'][-1] if st['last_word'] else '?')}`")
                    ))
            # regardless, we don't process further if the message was in task-channel
            return

        # If not active or not in the game channel, ignore
        if not st["active"]:
            return
        if message.channel.id != st["channel_id"]:
            return

        # If game paused, inform that game is paused and ignore message
        if st.get("paused"):
            await message.channel.send(embed=self.make_embed(
                description="🛑 Het spel is momenteel gepauzeerd — er staat een taak klaar in het taak-kanaal."
            ))
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
                # fout begonnen met verkeerde letter -> pauze en taak toewijzen
                await self._assign_task_for_incorrect(
                    message.guild, message.author, message.channel,
                    f"Het woord moest beginnen met `{required}`, maar je begon met `{content}`.",
                    previous_last_word=st["last_word"]
                )
                return

        # Check of het woord bestaat
        if not self.nl_dict.check(content):
            # ongeldig woord -> pauze en taak toewijzen
            await self._assign_task_for_incorrect(
                message.guild, message.author, message.channel,
                f"`{content}` is geen geldig Nederlands woord!",
                previous_last_word=st["last_word"]
            )
            return

        # Correct woord
        st["current_score"] += 1
        st["last_word"] = content
        st["last_user_id"] = message.author.id

        await message.channel.send(embed=self.make_embed(
            description=(f"✅ {message.author.display_name} heeft het woord `{content}` getypt!\n"
                         f"Start het volgende woord met de laatste letter\n"
                         f"Huidige score: {st['current_score']}\nDoel: {st['goal_points']}")
        ))

        # Check doelpunten
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

    # -------------------- Task assignment / timeout --------------------
    async def _assign_task_for_incorrect(self, guild: discord.Guild, user: discord.Member, game_channel: discord.TextChannel,
                                         reason_text: str, previous_last_word: Optional[str]):
        """Zet het spel op pauze en post een taak in het taak-kanaal."""
        st = self._get_state(guild.id)
        gd = self._get_guild_data(guild.id)

        # If there's already a pending task, inform user
        if st.get("paused") and st.get("pending_task"):
            await game_channel.send(embed=self.make_embed(
                description="🛑 Er is al een openstaande taak — los die eerst op voordat je nieuwe fouten maakt."
            ))
            return

        # choose a task
        tasks_list = gd.get("tasks", [])
        if not tasks_list:
            chosen = "Typ een bericht om verder te gaan."
        else:
            chosen = random.choice(tasks_list)

        # set paused state and store pending task
        st["paused"] = True
        st["pending_task"] = {
            "user_id": user.id,
            "task_text": chosen,
            "assigned_at": asyncio.get_event_loop().time()
        }
        # keep last_word intact to show to users
        st["last_word"] = previous_last_word
        st["last_user_id"] = user.id

        # notify game channel
        await game_channel.send(embed=self.make_embed(
            title="🛑 Fout woord — Spel gepauzeerd",
            description=(f"❌ {user.mention} — {reason_text}\n\n"
                         f"Er is een taak toegewezen aan {user.mention}. Ga naar het taak-kanaal om de taak uit te voeren.\n\n"
                         f"Laatste correcte woord: `{previous_last_word or 'geen'}`")
        ))

        # post in task channel if configured
        task_channel_id = gd.get("task_channel_id")
        task_ch = None
        if task_channel_id:
            task_ch = guild.get_channel(task_channel_id)
            if task_ch:
                await task_ch.send(embed=self.make_embed(
                    title="📝 Taak toegewezen",
                    description=(f"{user.mention}, je hebt een taak om het spel te hervatten:\n\n"
                                 f"> {chosen}\n\n"
                                 "Typ een bericht in dit kanaal zodra je de taak hebt uitgevoerd.\n"
                                 f"Als je binnen {gd.get('timeout_seconds', DEFAULT_TIMEOUT)} seconden niets doet, gaat het spel automatisch verder.")
                ))
            else:
                # invalid channel
                await game_channel.send(embed=self.make_embed(
                    description="❗ Taak-kanaal is niet correct geconfigureerd of niet gevonden. Gebruik `$ws taskchannel #kanaal`."
                ))

        else:
            await game_channel.send(embed=self.make_embed(
                description="❗ Er is geen taak-kanaal ingesteld. Gebruik `$ws taskchannel #kanaal` om er één in te stellen."
            ))

        # schedule timeout handler and store task handle
        timeout_seconds = gd.get("timeout_seconds", DEFAULT_TIMEOUT)
        th = asyncio.create_task(self._task_timeout_handler(guild.id, timeout_seconds))
        st["pending_task"]["timeout_handle"] = th

    async def _task_timeout_handler(self, guild_id: int, timeout_seconds: int):
        """Wacht timeout_seconds; als taak nog niet voltooid, hervat het spel automatisch."""
        try:
            await asyncio.sleep(timeout_seconds)
            st = self._get_state(guild_id)
            if not st.get("paused") or not st.get("pending_task"):
                return  # already resolved

            pending = st["pending_task"]
            user_id = pending.get("user_id")
            # clear pending task
            st["paused"] = False
            st["pending_task"] = None

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            gd = self._get_guild_data(guild_id)

            game_ch = guild.get_channel(st["channel_id"]) if st.get("channel_id") else None
            task_ch = guild.get_channel(gd.get("task_channel_id")) if gd.get("task_channel_id") else None

            # send timeout notices
            if task_ch:
                await task_ch.send(embed=self.make_embed(
                    title="⏱️ Taak verlopen",
                    description=(f"<@{user_id}> heeft de taak niet op tijd uitgevoerd — het spel gaat weer verder.\n\n"
                                 f"Laatste correcte woord: `{st['last_word'] or 'geen'}`")
                ))
            if game_ch:
                await game_ch.send(embed=self.make_embed(
                    title="▶️ Spel hervat (time-out)",
                    description=(f"De taak van <@{user_id}> is niet uitgevoerd binnen de tijd — het spel gaat verder.\n\n"
                                 f"Laatste correcte woord: `{st['last_word'] or 'geen'}`\n"
                                 f"Volgend woord moet beginnen met: `{(st['last_word'][-1] if st['last_word'] else '?')}`")
                ))
        except asyncio.CancelledError:
            # timeout cancelled because task completed — ignore
            return
        except Exception as e:
            print(f"[WoordSpelV2] Error in timeout handler for {guild_id}: {e}")
            return

# EOF
