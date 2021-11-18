from pathlib import Path

from decouple import config
from discord.ext import commands

ROOT_DIR = Path(__file__).resolve(strict=True).parent

bot = commands.Bot(command_prefix=config("DISCORD_PREFIX"))


@bot.command()
async def ping(ctx):
    await ctx.send("PONG")


# Register Cogs with bot
for cog in (ROOT_DIR / "cogs").glob("*.py"):
    print(f"Found cog: 'cog.{cog.name[:-3]}'")
    bot.load_extension(f"gainsworth.cogs.{cog.name[:-3]}")


bot.run(config("DISCORD_BOT_KEY"))
