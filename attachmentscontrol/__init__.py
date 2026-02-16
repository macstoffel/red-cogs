from .attachmentscontrol import AttachmentsControl

async def setup(bot):
    await bot.add_cog(AttachmentsControl(bot))