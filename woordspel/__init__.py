from .woordspel import Woordspel

def setup(bot):
    bot.add_cog(Woordspel(bot))
