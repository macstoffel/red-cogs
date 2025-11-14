from .woordspelv2 import WoordSpelV2

async def setup(bot):
    await bot.add_cog(WoordSpelV2(bot))
