import logging

from decouple import config
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)

from gainsworth.db.models import Base, Exercise, ResultType, User

class GainsMemory(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents the particular bot that is using the cog.
        """
        self.client = client
        self._last_member = None
        self.logger = logging.getLogger(__name__)
        self.logger.info('GainsMemory Cog instance created')
        self.engine = create_engine(config("DATABASE_URL"))

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global listeners,
        which means you can have multiple cogs listening for the same events and
        taking actions based on those events.
        """
        print("Gainsworth will now remember your gains!")


    @commands.command()
    async def hello(self, ctx):
        """Says hello"""
        channel = ctx.channel
        channels = ["gym-class-heroes"]
        if ctx.author == self.client.user:
            return
        if channel.name in channels:
            member = ctx.author
            if self._last_member is None or self._last_member.id != member.id:
                # {0.name} here comes from the MessageEmbed class's "fields" attr
                await ctx.send('Hello {0.name}~'.format(member))
            else:
                await ctx.send('Hello {0.name}... Are you getting your GAINS in?'.format(member))
            self._last_member = member


# allow user to register a new User based on the ctx.author.id
# allow user to add exercises to their User db entry (ask to define name, result type, reps=0, latest_date = today())
# allow user to increment exercises based on how many they did, update latest_date
# first, allow user to print all their total exercises:
    # eventually allow user to query their exercises and filter by exercises if they want



def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsMemory(client))
