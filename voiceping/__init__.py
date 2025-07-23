from .voiceping import VoicePing

async def setup(bot):
    await bot.add_cog(VoicePing(bot))
