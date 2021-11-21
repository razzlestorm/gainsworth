from pathlib import Path

from discord.ext import commands

from gainsworth.cogs.gainsworth_core import Gainsworth

bot = commands.Bot(command_prefix="$")

def test_logger():
    g = Gainsworth(bot)
    assert g.logger

def test_logfile():
    path = Path("gainsworth_debug.log")
    assert path.is_file()

def test_cog_loading():
    ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
    for cog in (ROOT_DIR / "cogs").glob("!(__init__)*.py"):
        print(f"Found cog: 'cog.{cog.name[:-3]}'")
        bot.load_extension(f"gainsworth.cogs.{cog.name[:-3]}")
