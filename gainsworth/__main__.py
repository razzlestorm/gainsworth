import logging
from pathlib import Path

from decouple import config
from discord.ext import commands

ROOT_DIR = Path(__file__).resolve(strict=True).parent

# Logging setup, cogs should ideally define their logger in their __init__.
logger = logging.getLogger('gainsworth')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('gainsworth_debug.log')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


bot = commands.Bot(command_prefix=config("DISCORD_PREFIX"))


@bot.event
async def on_ready():
    print("Gainsworth is activated!")

@bot.command()
async def ping(ctx):
    await ctx.send("PONG")


# Register Cogs with bot
init = ROOT_DIR/"cogs"/"__init__.py"
cogs = [cog for cog in (ROOT_DIR / "cogs").glob("*.py") if cog != init]
for cog in cogs:
    print(f"Found cog: 'cog.{cog.name[:-3]}'")
    bot.load_extension(f"gainsworth.cogs.{cog.name[:-3]}")

bot.run(config("DISCORD_BOT_KEY"))
