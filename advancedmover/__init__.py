from .advancedmover import AdvancedMover


async def setup(bot):
    await bot.add_cog(AdvancedMover(bot))