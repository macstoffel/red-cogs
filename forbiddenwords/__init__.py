from .forbiddenwords import ForbiddenWords


async def setup(bot):
    await bot.add_cog(ForbiddenWords(bot))
