# Re-export the cog setup so Red can await package.setup(bot)

from .bumpreminder import BumpReminder  # import the cog class

async def setup(bot):
    """Add the BumpReminder cog to the bot."""
    await bot.add_cog(BumpReminder(bot))
