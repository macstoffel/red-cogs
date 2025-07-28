from .timematchcog import TimeMatchCog

async def setup(bot):
    await bot.add_cog(TimeMatchCog(bot))