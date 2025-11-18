from .inactivekicker import InactiveKicker


async def setup(bot):
    await bot.add_cog(InactiveKicker(bot))
