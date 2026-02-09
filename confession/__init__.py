
from .confession import Confession

async def setup(bot):
    await bot.add_cog(Confession(bot))
