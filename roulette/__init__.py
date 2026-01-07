from .roulette import Roulette

async def setup(bot):
    self.tasks = load_tasks()  # laad taken bij starten
    await bot.add_cog(Roulette(bot))
