from .alphabetkink import AlphabetKink

async def setup(bot):
    await bot.add_cog(AlphabetKink(bot))
