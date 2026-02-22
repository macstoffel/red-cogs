from redbot.core import commands
import discord
import asyncio
from datetime import datetime, timedelta


class AdvancedMover(commands.Cog):
    """Production-ready message mover and copier with full thread support."""

    def __init__(self, bot):
        self.bot = bot

    # --------------------------------------------------
    # Utility Functions
    # --------------------------------------------------

    async def get_webhook(self, destination: discord.TextChannel | discord.Thread):
        webhooks = await destination.webhooks()
        for wh in webhooks:
            if wh.name == "AdvancedMover":
                return wh
        return await destination.create_webhook(name="AdvancedMover")

    async def confirm_large_action(self, ctx, count):
        if count <= 100:
            return True

        await ctx.send(
            f"⚠️ Je staat op het punt {count} berichten te verwerken.\n"
            f"Typ `ja` om te bevestigen."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", timeout=30, check=check)
            return reply.content.lower() == "ja"
        except asyncio.TimeoutError:
            await ctx.send("⏳ Tijd verstreken. Geannuleerd.")
            return False

    async def process(self, ctx, destination, messages, delete_original):
        count = len(messages)

        if count == 0:
            await ctx.send("Geen berichten gevonden.")
            return

        if not await self.confirm_large_action(ctx, count):
            return

        webhook = await self.get_webhook(destination)

        processed = 0
        failed = 0

        status_msg = await ctx.send(f"Start verwerking van {count} berichten...")

        for message in messages:
            try:
                files = [await a.to_file() for a in message.attachments]

                await webhook.send(
                    content=message.content or "",
                    username=message.author.display_name,
                    avatar_url=message.author.display_avatar.url,
                    embeds=message.embeds,
                    files=files,
                )

                if delete_original:
                    await message.delete()

                processed += 1

                if processed % 10 == 0:
                    await status_msg.edit(
                        content=f"Verwerkt: {processed}/{count}"
                    )

                await asyncio.sleep(0.25)

            except Exception:
                failed += 1

        await status_msg.edit(
            content=f"✅ Klaar!\nVerwerkt: {processed}\n❌ Mislukt: {failed}"
        )

    async def collect_messages(
        self,
        channel,
        start_id=None,
        end_id=None,
        member=None,
        minutes=None,
    ):
        results = []

        threshold = None
        if minutes:
            threshold = datetime.utcnow() - timedelta(minutes=minutes)

        async for msg in channel.history(limit=None, oldest_first=True):
            if start_id and msg.id < start_id:
                continue
            if end_id and msg.id > end_id:
                continue
            if member and msg.author != member:
                continue
            if threshold and msg.created_at < threshold:
                continue

            results.append(msg)

        return results

    async def find_message_global(self, guild, message_id: int):
        # Check text channels
        for channel in guild.text_channels:
            try:
                return await channel.fetch_message(message_id)
            except Exception:
                continue

        # Check active threads
        for thread in guild.threads:
            try:
                return await thread.fetch_message(message_id)
            except Exception:
                continue

        return None

    # --------------------------------------------------
    # Commands
    # --------------------------------------------------

    @commands.guild_only()
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def advmove(
        self,
        ctx,
        destination: discord.TextChannel | discord.Thread,
        member: discord.Member = None,
        minutes: int = None,
        start_id: int = None,
        end_id: int = None,
    ):
        """Geavanceerd verplaatsen met filters."""
        messages = await self.collect_messages(
            ctx.channel, start_id, end_id, member, minutes
        )
        await self.process(ctx, destination, messages, delete_original=True)

    @commands.guild_only()
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def advcopy(
        self,
        ctx,
        destination: discord.TextChannel | discord.Thread,
        member: discord.Member = None,
        minutes: int = None,
        start_id: int = None,
        end_id: int = None,
    ):
        """Geavanceerd kopiëren met filters."""
        messages = await self.collect_messages(
            ctx.channel, start_id, end_id, member, minutes
        )
        await self.process(ctx, destination, messages, delete_original=False)

    @commands.guild_only()
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def advmovetonewthread(self, ctx, *, thread_name: str):
        """Maak nieuwe thread en verplaats alles hierheen."""
        thread = await ctx.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread,
        )

        messages = await self.collect_messages(ctx.channel)
        await self.process(ctx, thread, messages, delete_original=True)

    @commands.guild_only()
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def moveid(
        self,
        ctx,
        destination: discord.TextChannel | discord.Thread,
        message_id: int,
    ):
        """Verplaats één specifiek bericht (server-breed zoeken)."""

        message = await self.find_message_global(ctx.guild, message_id)

        if not message:
            await ctx.send("❌ Bericht nergens gevonden in deze server.")
            return

        webhook = await self.get_webhook(destination)

        try:
            files = [await a.to_file() for a in message.attachments]

            await webhook.send(
                content=message.content or "",
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
                embeds=message.embeds,
                files=files,
            )

            await message.delete()

            await ctx.send(
                f"✅ Bericht verplaatst vanuit {message.channel.mention}"
            )

        except Exception as e:
            await ctx.send(f"❌ Fout bij verplaatsen: {e}")

    @commands.guild_only()
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def copyid(
        self,
        ctx,
        destination: discord.TextChannel | discord.Thread,
        message_id: int,
    ):
        """Kopieer één specifiek bericht (server-breed zoeken)."""

        message = await self.find_message_global(ctx.guild, message_id)

        if not message:
            await ctx.send("❌ Bericht nergens gevonden in deze server.")
            return

        webhook = await self.get_webhook(destination)

        try:
            files = [await a.to_file() for a in message.attachments]

            await webhook.send(
                content=message.content or "",
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
                embeds=message.embeds,
                files=files,
            )

            await ctx.send(
                f"✅ Bericht gekopieerd vanuit {message.channel.mention}"
            )

        except Exception as e:
            await ctx.send(f"❌ Fout bij kopiëren: {e}")