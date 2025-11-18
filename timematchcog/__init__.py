# filepath: /Users/krh0812/Documents/GitHub/red-cogs/timematchcog/__init__.py
from .timematchcog import TimeMatchCog

async def setup(bot):
    await bot.add_cog(TimeMatchCog(bot))