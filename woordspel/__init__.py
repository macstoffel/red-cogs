from .woordspel import Woordspel

async def setup(bot):
    await bot.add_cog(Woordspel(bot))
