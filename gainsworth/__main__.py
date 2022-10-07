import asyncio
import logging
from pathlib import Path
import sys
import time

import discord

from decouple import config
from discord.ext import commands

ROOT_DIR = Path(__file__).resolve(strict=True).parent

# Logging setup, cogs should ideally define their logger in their __init__.
logger = logging.getLogger('gainsworth')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('gainsworth_debug.log')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = config("DISCORD_PREFIX"), intents = discord.Intents.default())

    async def on_ready(self):
        print(f"We have logged in as {self.user}.")


    # #METHOD 1: "Auto-Syncing" (sync only when you need to: modifying app commands' server-end info, like their name or description) - ratelimit for syncing is twice per minute
    # async def setup_hook(self):
    #     # init = ROOT_DIR/"cogs"/"__init__.py"
    #     # cogs = [cog for cog in (ROOT_DIR / "cogs").glob("*.py") if cog != init]
    #     # for cog in cogs:
    #     #     print(f"Found cog: 'cog.{cog.name[:-3]}'")
    #     #     await self.load_extension(f"gainsworth.cogs.{cog.name[:-3]}")
    #     await self.tree.sync(guild = discord.Object(id=740310401001980036)) #make this line a comment, if you don't need to sync
    #     print("Synced!")

bot = Bot()


# bot = commands.Bot(command_prefix=config("DISCORD_PREFIX"), intents=intents)

async def load_cogs(b):
    init = ROOT_DIR/"cogs"/"__init__.py"
    cogs = [cog for cog in (ROOT_DIR / "cogs").glob("*.py") if cog != init]
    for cog in cogs:
        print(f"Found cog: 'cog.{cog.name[:-3]}'")
        await b.load_extension(f"gainsworth.cogs.{cog.name[:-3]}")

# @bot.event
# async def on_ready():
#     # Register Cogs with bot
#     commands = await bot.tree.sync(guild=discord.Object(id="740310401001980036"))
#     # bot.tree.clear_commands(guild=discord.Object(id="740310401001980036"))
#     print(await bot.tree.fetch_commands(guild=discord.Object(id="740310401001980036")))
#     print(f"Gainsworth synced these commands: {commands}")
#     print("Gainsworth is finished loading!")



async def main():
    async with bot:
        await load_cogs(bot)
        await bot.start(config("DISCORD_BOT_KEY"))

asyncio.run(main())

# bot.run(config("DISCORD_BOT_KEY"))