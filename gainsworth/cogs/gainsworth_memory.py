from datetime import datetime
import logging

from decouple import config
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gainsworth.db.models import Exercise, User


engine = create_engine(config("DATABASE_URL"))
Session = sessionmaker(bind=engine)


class GainsMemory(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents
        the particular bot that is using the cog.
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound,)
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.name}, there was an issue with that command,'
                           ' type !help example_command to learn more about how'
                           ' to format the command')
        elif "duplicate key" in str(error):
            await ctx.send(f'That exercise already exists for you, {ctx.author.name}!'
                           ' Type !list_exercises to see all the exercises you have'
                           ' already added.')
        else:
            await ctx.send(f'{ctx.author.name}, something went wrong with your input.')

    # allow user to register a new User based on the ctx.author.id
    @commands.command()
    async def register(self, ctx):
        """
        This commands registers your username with Gainsworth, so the bot will
        remember you. Once you've registered, you can try the !create_exercise
        command to attach an exercise to your username. Also try !list_exercises
        to see the exercises that Gainsworth is currently remembering for you.
        """
        user = f"{ctx.author.name}#{ctx.author.discriminator}"
        channel = ctx.channel
        channels = ["gym-class-heroes"]
        if ctx.author == self.client.user:
            return
        if channel.name in channels:
            ses = Session()
            registered_user = ses.query(User).filter(User.name == user).first()
        if not registered_user:
            name = User(name=user, date_created=datetime.today())
            ses.add(name)
            ses.commit()
            ses.close()
            await ctx.send(f'{ctx.author.name}, you are now registered with Gainsworth,'
                           ' and can use !create_exercise. Type !help'
                           ' create_exercise to learn more.')
        elif registered_user:
            await ctx.send(f'{ctx.author.name}, you are already registered, type !help'
                           ' create_exercise to learn more!')

    # allow user to add exercises to their User db entry
    # (ask to define name, result type, reps=0, latest_date = today())
    @commands.command()
    async def create_exercise(self, ctx, name, unit=None):
        """
        Use this command to create a custom exercise that you can then !add_gains to.
        Gainsworth will remember your gains on the various exercises that you have \
        added. please specify the name and unit of measure for your exercise. Leave
        the unit of measure blank for quantity-based exercises. An example command
        might look like this: \n
        !create_exercise pushups\n         Or:\n        !create_exercise plank seconds
        """
        user = f"{ctx.author.name}#{ctx.author.discriminator}"
        if ctx.author == self.client.user:
            return
        ses = Session()
        registered_user = ses.query(User).filter(User.name == user).first()
        if not registered_user:
            await ctx.send(f"{ctx.author.name}, you haven't registered with"
                           " Gainsworth yet, try using the !register command first.")
        else:
            exercise = Exercise(name=name,
                                reps=0,
                                unit=unit,
                                latest_date=datetime.today(),
                                user_id=registered_user.id)
            ses.add(exercise)
            ses.commit()
            ses.close()
            await ctx.send(f"{ctx.author.name}, your exercise has been created! You"
                           " can now keep track of your daily gains with the"
                           f" !add_gains command. Example: !add_gains 10 {name}.")

    @commands.command()
    async def list_exercises(self, ctx):
        """
        This command lists the exercises that Gainsworth is remembering for you.
        """
        pass

    # allow user to increment exercises based on how many they did, update latest_date
    @commands.command()
    async def add_gains(self, ctx, amount, exercise):
        pass

    # first, allow user to print all their total exercises:
    @commands.command()
    async def list_gains(self, ctx):
        pass
    # eventually allow user to query their exercises and filter by exercises if they want


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsMemory(client))
