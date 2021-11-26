from datetime import datetime
import logging

from decouple import config
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gainsworth.db.models import Base, Exercise, ResultType, User


engine = create_engine(config("DATABASE_URL"))
Session = sessionmaker(bind=engine)

class GainsMemory(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents the particular bot that is using the cog.
        """
        self.client = client
        self._last_member = None
        self.logger = logging.getLogger(__name__)
        self.logger.info('GainsMemory Cog instance created')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global listeners,
        which means you can have multiple cogs listening for the same events and
        taking actions based on those events.
        """
        print("Gainsworth will now remember your gains!")
    
    # allow user to register a new User based on the ctx.author.id
    @commands.command()
    async def register_user(self, ctx):
        self.logger.info('Message received')
        print("message received")
        breakpoint()
        user = ctx.author.id
        channel = ctx.channel
        channels = ["gym-class-heroes"]
        if ctx.author == self.client.user:
            return
        if channel.name in channels:
            ses = Session()
            if not lookup_user(ses, user):
                name = User(name=user, date_created=datetime.today())
                ses.add(name)
                ses.commit()
                ses.close()
                await ctx.send('{0.name}, you are now registered with Gainsworth, and can !create_new exercises. Type !help create_new to learn more.'.format(user))
    
"""
# allow user to add exercises to their User db entry (ask to define name, result type, reps=0, latest_date = today())
@commands.command()
async def create_new(self, ctx):
    pass
# allow user to increment exercises based on how many they did, update latest_date
@commands.command()
async def count(self, ctx):
    pass
# first, allow user to print all their total exercises:
@commands.command()
async def totals(self, ctx):
    pass
# eventually allow user to query their exercises and filter by exercises if they want
"""
"""
def lookup_user(self, session, username):
    return session.query(User).filter(User.name == username).value
"""
def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsMemory(client))
