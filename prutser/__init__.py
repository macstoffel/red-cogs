from .prutser import Prutser

async def setup(bot):
    await bot.add_cog(Prutser(bot))