from .loggingcog import LoggingCog

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
