from redbot.core import commands
from .woordspelv3 import WoordSpelV3


__red_end_user_data_statement__ = (
    "Deze cog slaat alleen spelgegevens op die nodig zijn voor functionaliteit, "
    "zoals scores en instellingen per server. Er worden geen persoonlijke gegevens "
    "van gebruikers opgeslagen buiten Discord-ID's."
)


async def setup(bot: commands.Bot):
    await bot.add_cog(WoordSpelV3(bot))
