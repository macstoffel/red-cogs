from .bumpreminder import BumpReminder

def setup(bot):
    bot.add_cog(BumpReminder(bot))
