from datetime import date, timedelta
import json
import logging
from os.path import exists
import pathlib
import re
import sys

from decouple import config
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from sqlalchemy.sql import func

from sqlalchemy import create_engine, func, update
from sqlalchemy.orm import sessionmaker

from gainsworth.db.models import Exercise, User


engine = create_engine(config("DATABASE_URL"))
Session = sessionmaker(bind=engine)

DEFAULT_REMOVAL=date.today() - timedelta(weeks=52)

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
        removed = []
        memory = self.client.get_cog("GainsMemory")
        ses = Session()
        users = ses.query(User).all()
        for user in users:
            if not user:
                continue
            # checking for null value
            if not user.last_active:
                user.last_active = func.now()
                ses.commit()
            if user.auto_remove and user.last_active.date() < DEFAULT_REMOVAL:
                try:
                    removed.append(user.user_id)
                    target = ses.query(User).filter(User.user_id == user.user_id).delete()
                except Exception as e:
                    self.logger.error(f"Failed to remove user; {e}")
        #TODO: make sure this loop runs again on DC, and after init
        print("Inactive check completed")
        self.logger.info("list of IDs removed: {removed}")

    @remove_inactive.before_loop
    async def before_remove_inactive(self):
        print("waiting...")
        await self.client.wait_until_ready()


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsClock(client))
