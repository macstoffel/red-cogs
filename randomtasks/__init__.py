from .randomtasks import RandomTasks

async def setup(bot):
    await bot.add_cog(RandomTasks(bot))
