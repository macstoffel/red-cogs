from .quiz import Quiz

async def setup(bot):
    await bot.add_cog(Quiz(bot))
