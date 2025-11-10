from .woordspel_td import WoordspelTD

async def setup(bot):
    await bot.add_cog(WoordspelTD(bot))
