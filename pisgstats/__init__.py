from .pisgstats import PisgStats

async def setup(bot):
    await bot.add_cog(PisgStats(bot))
