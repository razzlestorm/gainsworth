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