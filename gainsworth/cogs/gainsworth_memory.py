from datetime import datetime
from decimal import Decimal
import logging

from decouple import config
from discord.ext import commands
from sqlalchemy import create_engine, func
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
        ignored = (commands.CommandInvokeError)
        
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'{ctx.author.name}, I did not understand that command.'
                           'Try typing `!help` to see a list of available commands.')
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.name}, there was an issue with that command,'
                           ' type `!help example_command` to learn more about how'
                           ' to format a command')
        # It's probably better to handle these errors in their respective methods
        elif "'NoneType' object has no attribute 'reps'" in str(error):
            await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                " Type `!list_exercises` to see all the exercises I'm currently"
                ' tracking.')          
        elif "duplicate key" in str(error):
            await ctx.send(f'That exercise already exists for you, {ctx.author.name}!'
                           ' Type `!list_exercises` to see all the exercises you have'
                           ' already added.')
        elif "UnmappedInstanceError" in str(error):
            await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                " Type `!list_exercises` to see all the exercises I'm currently"
                ' tracking.')
        elif isinstance(error, ignored):
            return
        else:
            await ctx.send(f'{ctx.author.name}, something went wrong with your input.')

    async def _check_registered(self, ctx):
        user = f"{ctx.author.name}#{ctx.author.discriminator}"
        if ctx.author == self.client.user:
            return
        ses = Session()
        registered_user = ses.query(User).filter(User.name == user).first()
        if not registered_user:
            ses.close()
            await ctx.send(f"{ctx.author.name}, you haven't registered with"
                           " Gainsworth yet, try using the `!register` command first.")
        else:
            return ses, registered_user

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
                name = User(name=user, date_created=datetime.utcnow())
                ses.add(name)
                ses.commit()
                ses.close()
                await ctx.send(f'{ctx.author.name}, you are now registered with'
                               ' Gainsworth, and can use `!create_exercise`. Type'
                               ' `!help create_exercise` to learn more.')
            else:
                await ctx.send(f'{ctx.author.name}, you are already registered, type'
                               ' !help create_exercise to learn more!')

    @commands.command()
    async def create_exercise(self, ctx, name, unit=None):
        """
        Use this command to create a custom exercise that you can then !add_gains to.
        Gainsworth will remember your gains on the various exercises that you have
        added. Please specify the name and unit of measure for your exercise. Leave
        the unit of measure blank for quantity-based exercises. Your exercise name
        should be just one word. An example command might look like this: \n
        !create_exercise Pushups\n\n        Or:\n\n      !create_exercise Planks minutes
        \n\n    Or:\n\n    !create_exercise JumpingJacks
        """
        ses, user = await self._check_registered(ctx)
        if user:
            if ses.query(Exercise).filter(Exercise.user_id == user.id).filter(Exercise.name == name).first():
                await ctx.send(f'That exercise already exists for you, {ctx.author.name}!'
                           ' Type `!list_exercises` to see all the exercises you have'
                           ' already added.')
            else:
                exercise = Exercise(name=name,
                                    reps=0,
                                    unit=unit,
                                    date=datetime.utcnow(),
                                    user_id=user.id)
                ses.add(exercise)
                self.logger.info(f"New type of exercise created: {exercise}")
                ses.commit()
                ses.close()
                await ctx.send(f"{ctx.author.name}, your exercise has been created! You"
                            " can now keep track of your daily gains with the"
                            f" `!add_gains` command. Example: !add_gains 10 {name}.")
        else:
            ses.close()
            return

    @commands.command()
    async def list_exercises(self, ctx):
        """
        This command lists the exercises that Gainsworth is remembering for you.
        """
        ses, user = await self._check_registered(ctx)
        if user:
            exercises = [(e.name, e.unit) for e in user.exercises]
            exercises = set(exercises)
            if len(exercises) < 1:
                ses.close()
                await ctx.send(f"{ctx.author.name}, it looks like you haven't created"
                               " any exercises! Type `!help create_exercise` to get"
                               " started!")
            else:
                formatted_exercises = []
                for tup in exercises:
                    if tup[1]:
                        formatted_exercises.append(f"{tup[0]} (in {tup[1]})")
                    else:
                        formatted_exercises.append(f"{tup[0]}")
                formatted_exercises = "\n".join(formatted_exercises)
                ses.close()
                await ctx.send(f"{ctx.author.name}, here is a list of your exercises!\n"
                               f"{formatted_exercises}")
        else:
            ses.close()
            return

    @commands.command()
    async def remove_exercise(self, ctx, exercise):
        """
        Use this command to remove ALL exercises of a certain name that you've been 
        tracking from Gainsworth's memory banks. BEWARE! This will remove all gains
        associated with that exercise that you've recorded.
        An example command might look like this: \n
        !remove_exercise Pushups\n\n
        """
        ses, user = await self._check_registered(ctx)
        if user:
            remove_target = ses.query(Exercise).filter(Exercise.user_id == user.id).filter(Exercise.name == exercise).delete()
            self.logger.info(f"records deleted: {remove_target}")
            total_removed = str(remove_target)
            ses.commit()
            ses.close()
            await ctx.send(f"{ctx.author.name}, your **{total_removed}** exercise"
                               f" records of **{exercise}** were deleted. You can type"
                               " `!list_exercises` to see which exercises I'm keeping"
                               " track of, or `!help create_exercise` to see how you"
                               " start tracking anew one!")
        else:
            ses.close()
            return

    @commands.command()
    async def add_gains(self, ctx, amount, exercise):
        """
        Use this command to tell Gainsworth about an exercise that you did!
        Gainsworth will keep a record of your exercise, how much of that 
        exercise you did, and what day you did it on (in UTC time). This will let you
        keep track of how your gains improve over time!
        An example command might look like this: \n
        !add_gains 10 Pushups\n\n        Or:\n\n      !add_gains 1.5 Planks\n\n
        """
        ses, user = await self._check_registered(ctx)
        if user:
            exercises = [e.name for e in user.exercises]
            if exercise in exercises:
                unit = ses.query(Exercise).filter(Exercise.user_id == user.id).filter(Exercise.name == exercise).first().unit
                gain = Exercise(name=exercise,
                                reps=Decimal(amount),
                                unit=unit,
                                date=datetime.utcnow(),
                                user_id=user.id)
                ses.add(gain)
                self.logger.info(f"New gain added: {gain}")
                ses.commit()
                ses.close()
                # Some string formatting handling
                unit_handler = ""
                if not exercise.endswith("s"):
                    exercise = exercise + "s"
                if unit:
                    unit = " " + str(unit)
                    unit_handler = "of "
                elif not unit:
                    unit = ""
                await ctx.send(f"{ctx.author.name}, I've recorded your {amount}{unit}"
                                f" {unit_handler}{exercise}. Awesome work! Try typing"
                                " `!list_gains` to see the totals of your exercises!")
            else:
                await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                    " Type `!list_exercises` to see all the exercises I'm currently"
                    ' tracking.')
        else:
            ses.close()
            return

    @commands.command()
    async def list_gains(self, ctx):
        """
        Use this command to tell yourself and everyone else how awesome you are! 
        Gainsworth will list out all the gains that you have recorded with the
        !add_gains command.
        """
        ses, user = await self._check_registered(ctx)
        if user:
            exercise_objs = [e for e in user.exercises]
            if len(exercise_objs) < 1:
                ses.close()
                await ctx.send(f"{ctx.author.name}, it looks like you haven't created"
                               " any exercises! Type `!help create_exercise` to get"
                               " started!")
            else:
                totals = []
                result = [x for x in ses.query(Exercise.name, Exercise.unit, func.sum(Exercise.reps)).filter(Exercise.user_id == user.id).group_by(Exercise.name, Exercise.unit).all()]
                for name, unit, reps in result:
                    e_name = name
                    if not e_name.endswith("s"):
                        e_name = e_name + "s"
                    if unit:
                        totals.append(f"{reps} {unit} of {e_name}")
                    else:
                        totals.append(f"{reps} {e_name}")
                msg = "You've done a total of:\n"
                msg += "\n".join(totals)
                ses.close()
                await ctx.send(f"{ctx.author.name}, here is a list of your totals!\n"
                               f"{msg}\n Keep up the **great gains** you're making!")

        else:
            ses.close()
            return
    # eventually allow user to query their exercises and filter by exercises if they want


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsMemory(client))
