from .channelbackup import ChannelBackup

async def setup(bot):
    await bot.add_cog(ChannelBackup(bot))# Init for ChannelBackup cog
