from datetime import datetime
from decimal import Decimal
import logging
import sys

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
        sys.stdout.write("Command Error: ")
        sys.stdout.write(f"{error}")
        ignored = (commands.CommandInvokeError)
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'{ctx.author.name}, I did not understand that command.'
                           ' Try typing `g!help` to see a list of available commands.')
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.name}, there was an issue with that command,'
                           f' type `g!help {ctx.args[1].command.name}` to learn more'
                           ' about how to format that command')
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(f'{ctx.author.name}, there was an issue with your arguments,'
                           f' type `g!help {ctx.args[1].command.name}` to learn more'
                           ' about how to format that command')
        # It's probably better to handle these errors in their respective methods
        elif "'NoneType' object has no attribute 'reps'" in str(error):
            await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                           " Type `g!list_exercises` to see all the exercises I'm"
                           " currently tracking.")
        elif "duplicate key" in str(error):
            await ctx.send(f'That exercise already exists for you, {ctx.author.name}!'
                           ' Type `g!list_exercises` to see all the exercises you have'
                           ' already added.')
        elif "UnmappedInstanceError" in str(error):
            await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                           " Type `g!list_exercises` to see all the exercises I'm"
                           " currently tracking.")
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
            name = User(name=user, date_created=datetime.utcnow())
            ses.add(name)
            ses.commit()
            registered_user = ses.query(User).filter(User.name == user).first()
        return ses, registered_user

    @commands.command(aliases=["ce", "create_e", "c_exercise"])
    async def create_exercise(self, ctx, name, unit=None):
        """
        Use this command to create a custom exercise that you can then !add_gains to.
        Gainsworth will remember your gains on the various exercises that you have
        added. Please specify the name and unit of measure for your exercise. Leave
        the unit of measure blank for quantity-based exercises. Your exercise name
        should be just one word. An example command might look like this: \n
        !create_exercise Pushups\n\nOr:\n\n!create_exercise Planks minutes\n\n
        Or:\n\n!create_exercise Jumping-Jacks\n\n
        **Remember**: Capitalization matters!
        """
        ses, user = await self._check_registered(ctx)
        if user:
            if ses.query(Exercise).filter(Exercise.user_id == user.id).filter(Exercise.name == name).first():
                await ctx.send(f'That exercise already exists for you,'
                               f' {ctx.author.name}! Type `g!list_exercises` to see all'
                               ' the exercises you have already added.')
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
                               " `g!add_gains` command."
                               f" Example: g!add_gains 10 {name}.")
        else:
            ses.close()
            return

    @commands.command(aliases=["le", "list_e", "l_exercises"])
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
                               " any exercises! Type `!ghelp create_exercise` to get"
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

    @commands.command(aliases=["re", "remove_e", "r_exercise"])
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
            # minus the Exercise made by g!ce
            total_removed = int(str(remove_target)) - 1
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

    @commands.command(aliases=["ag", "add_g", "a_gains"])
    async def add_gains(self, ctx, *args):
        """
        Use this command to tell Gainsworth about an exercise that you did!
        Gainsworth will keep a record of your exercise, how much of that
        exercise you did, and what day you did it on (in UTC time). This will let you
        keep track of how your gains improve over time!
        An example command might look like this: \n
        !add_gains 10 pushups\n\n        Or:\n\n      !add_gains 1.5 planks\n\n
        """
        ses, user = await self._check_registered(ctx)
        # Implement better checking
        if len(args) > 2:
            raise commands.ArgumentParsingError()
        amount = [arg for arg in args if arg.isdigit()][0]
        exercise = [arg for arg in args if not arg.isdigit()][0]
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
                if unit:
                    unit = " " + str(unit)
                    unit_handler = "of "
                elif not unit:
                    unit = ""
                await ctx.send(f"{ctx.author.name}, I've recorded your {amount}{unit}"
                               f" {unit_handler}{exercise}. Awesome work! Try typing"
                               " `g!list_gains` to see the totals of your exercises!")
            else:
                await ctx.send(f"I didn't find that exercise, {ctx.author.name}!"
                               " Type `g!list_exercises` to see all the exercises I'm"
                               " currently tracking.")
        else:
            ses.close()
            return

    @commands.command(aliases=["lg", "list_g", "l_gains"])
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
                               " any exercises! Type `g!help create_exercise` to get"
                               " started!")
            else:
                totals = []
                result = [x for x in ses.query(Exercise.name, Exercise.unit, func.sum(Exercise.reps)).filter(Exercise.user_id == user.id).group_by(Exercise.name, Exercise.unit).all()]
                for name, unit, reps in result:
                    if unit:
                        totals.append(f"{reps} {unit} of {name}")
                    else:
                        totals.append(f"{reps} {name}")
                msg = "You've done a total of:\n"
                msg += "\n".join(totals)
                ses.close()
                await ctx.send(f"{ctx.author.name}, here is a list of your totals!\n"
                               f"{msg}\nKeep up the **great gains** you're making!")

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
