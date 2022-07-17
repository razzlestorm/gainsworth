import json
import logging
from os.path import exists
import pathlib
import re
import sys
import discord
from discord.ext import commands, tasks


class GainsClock(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents
         the particular bot that is using the cog.
        """
        self.client = client
        self._last_member = None
        self.remove_inactive.start()
        self.logger = logging.getLogger(__name__)

        self.logger.info('Gainsworth Cog instance created')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global
         listeners, which means you can have multiple cogs listening for the
        same events and taking actions based on those events.
        """
        print("Gainsworth's clock is ticking...")

    @tasks.loop(hours=24.0)
    async def remove_inactive(self):
        memory = self.client.get_cog("GainsMemory")
        # make sure this loop runs again on DC, and after init
        # check user.auto_remove AND user.last_active
        # if we hit on the inactivity time and bool
        # call memory's remove_me_please
        # log removal
        self.logger.info()




def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(Gainsworth(client))
