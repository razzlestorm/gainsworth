from datetime import datetime, timedelta
from decimal import Decimal
import logging

from decouple import config
from discord.ext import commands
from sqlalchemy import create_engine, func, update
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

    async def _check_registered(self, ctx):
        user_name = f"{ctx.author.name}#{ctx.author.discriminator}"
        if ctx.author == self.client.user:
            return
        ses = Session()
        user_id = ctx.author.id
        registered_id = ses.query(User).filter(User.user_id == user_id).first()
        if not registered_id:
            registered_username = ses.query(User).filter(User.name == user_name).first()
            if not registered_username:
                name = User(name=user_name,
                            user_id=user_id,
                            date_created=datetime.utcnow(),
                            last_active=datetime.utcnow())
                ses.add(name)
                ses.commit()
            if not registered_username.user_id:
                registered_username.user_id = user_id
                ses.commit()
            registered_id = ses.query(User).filter(User.user_id == user_id).first()
        if registered_id.name != user_name:
            registered_id.name = user_name
            ses.commit()
        # add logic for updating username checking registered_id AND registered_username == current_username
        return ses, registered_id

    async def _add_gain(self, ses, user, amt, exercise):
        unit = ses.query(Exercise).filter(Exercise.user_id == user.id) \
               .filter(Exercise.name == exercise).first().unit
        gain = Exercise(name=exercise,
                        reps=Decimal(amt),
                        unit=unit,
                        date=datetime.utcnow(),
                        user_id=user.id)
        ses.add(gain)
        self.logger.info(f"New gain added: {gain}")
        user.last_active = datetime.utcnow()
        ses.commit()
        return ses, unit

    @commands.command(aliases=["ag", "AG", "Ag", "add_g", "a_gains"])
    async def add_gains(self, ctx, *args):
        """
        Tell Gainsworth about an activity that you did!
        Gainsworth will keep a record of your activity, how much of that
        activity you did, and what day you did it on (in UTC time). This will let you
        keep track of how your gains improve over time!
        An example command might look like this: \n
        g!add_gains 10 Pushups\n
        Or:\n
        g!add_gains 1.5 Planks, 100 Situps, 50 Pushups\n
        Or if you'd like to remove an erroneous entry:\n
        g!add_gains -10 Pushups\n
        """
        ses, user = await self._check_registered(ctx)
        if len(args) % 2:
            raise commands.ArgumentParsingError()
        arg_pairs = [(args[ii], args[ii+1]) for ii in range(0, len(args)-1, 2)]
        if user:
            exercises = [e.name for e in user.exercises]
            msgs = []
            for pair in arg_pairs:
                amount, exercise = pair
                amount = amount.strip(",;. ")
                exercise = exercise.strip(",;. ")
                if exercise[-1].isdigit() and any([c.isalpha() for c in amount]):
                    exercise, amount = amount, exercise
                if exercise in exercises:
                    ses, unit = await self._add_gain(ses, user, amount, exercise)
                    # Some string formatting handling
                    unit_handler = ""
                    if unit:
                        unit = " " + str(unit)
                        unit_handler = "of "
                    elif not unit:
                        unit = ""
                    msgs.append(f"{amount}{unit} {unit_handler}{exercise}")
                else:
                    await ctx.send(f"I didn't find that activity, {exercise}, in your"
                                   f" list, {ctx.author.name}! Type `g!list_activities`"
                                   " to see all the activities I'm currently tracking.")
                    ses.close()
                    return
            msgs = "\n".join(msgs)
            ses.close()
            await ctx.send(f"{ctx.author.name}, I've recorded the following activity:"
                           f"\n{msgs}\nAwesome work! Try typing"
                           " `g!list_gains` or `g!see_gains` to see the totals"
                           " of your activities!")
        else:
            ses.close()
            return

    @commands.command(aliases=["ca", "Ca", "CA", "create_a", "c_activity"])
    async def create_activity(self, ctx, name, unit=None):
        """
        Create a custom activity that you can then !add_gains to.
        Gainsworth will remember your gains on the various activities that you have
        added. Please specify the name and (optional) unit of measure for your activity. 
        Leave the unit of measure blank for quantity-based activities. \n
        **Your activity name should be just one word**. \n
        An example command might look like this:
        \n
        g!create_activity Pushups\n
        Or:\n
        g!create_activity StudyingPython minutes\n
        Or:\n
        g!create_activity Jumping-Jacks\n\n
        **Remember**: Capitalization matters!
        """
        ses, user = await self._check_registered(ctx)
        if user:
            if ses.query(Exercise).filter(Exercise.user_id == user.id) \
               .filter(Exercise.name == name).first():
                await ctx.send(f'That activity already exists for you,'
                               f' {ctx.author.name}! Type `g!list_activities` to see all'
                               ' the activities you have already added.')
            else:
                exercise = Exercise(name=name,
                                    reps=0,
                                    unit=unit,
                                    date=datetime.utcnow(),
                                    user_id=user.id)
                ses.add(exercise)
                self.logger.info(f"New type of activity created: {exercise}")
                ses.commit()
                ses.close()
                await ctx.send(f"{ctx.author.name}, your activity has been created! You"
                               " can now keep track of your daily gains with the"
                               " `g!add_gains` command."
                               f" Example: g!add_gains 10 {name}.")
        else:
            ses.close()
            return

    @commands.command(aliases=["la", "La", "LA" "list_a", "l_activities"])
    async def list_activities(self, ctx):
        """
        List the activities that Gainsworth is remembering for you.
        """
        ses, user = await self._check_registered(ctx)
        if user:
            exercises = [(e.name, e.unit) for e in user.exercises]
            exercises = set(exercises)
            if len(exercises) < 1:
                ses.close()
                await ctx.send(f"{ctx.author.name}, it looks like you haven't created"
                               " any activities! Type `g!help create_activity` to get"
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
                await ctx.send(f"{ctx.author.name}, here is a list of your activities!\n"
                               f"{formatted_exercises}")
        else:
            ses.close()
            return

    @commands.command(aliases=["lg", "Lg", "LG", "list_g", "l_gains"])
    async def list_gains(self, ctx, *args):
        """
        Tell yourself and everyone else how awesome you are!
        Gainsworth will list out all the gains that you have recorded with the
        g!add_gains command.\n
        An example command might look like this: \n
        g!lg\n
        OR:\n
        g!list_gains month \n
        Supported times are: any number, 'day', 'week', 'month', 'quarter'/'season',
         'year'.\n
        All gains since you began tracking gains are listed by default,
        or if there is an erroneous time filter.
        """
        TIMES = {
            "today": 1, 
            "day": 1,
            "days": 1,
            "week": 7,
            "weeks": 7,
            "month": 30,
            "months": 30,
            "quarter": 90,
            "season": 90,
            "3month": 90,
            "3months": 90,
            "year": 365
        }
        ses, user = await self._check_registered(ctx)
        if user:
            exercise_objs = [e for e in user.exercises]
            if len(exercise_objs) < 1:
                ses.close()
                await ctx.send(f"{ctx.author.name}, it looks like you haven't created"
                               " any activities! Type `g!help create_activity` to get"
                               " started!")
            else:
                totals = []
                if len(args) == 1:
                    if args[0].lower() in TIMES:
                        days = TIMES.get(args[0].lower(), 1)
                    elif args[0].isdigit():
                        try:
                            days = int(args[0])
                        except ValueError:
                            days = int(float(args[0]))
                            
                    end = datetime.utcnow()
                    start = (end-timedelta(days=days))
                    result = [x for x in ses.query(Exercise.name,
                                                Exercise.unit,
                                                func.sum(Exercise.reps))
                            .filter(Exercise.user_id == user.id)
                            .filter(Exercise.date >= start)
                            .group_by(Exercise.name, Exercise.unit).all()]
                else:
                    start = user.date_created
                    result = [x for x in ses.query(Exercise.name,
                                                Exercise.unit,
                                                func.sum(Exercise.reps))
                            .filter(Exercise.user_id == user.id)
                            .group_by(Exercise.name, Exercise.unit).all()]
                for name, unit, reps in result:
                    if unit:
                        totals.append(f"{reps} {unit} of {name}")
                    else:
                        totals.append(f"{reps} {name}")
                msg = f"Since {start.date()}, you've done a total of:\n"
                msg += "\n".join(totals)
                ses.close()
                await ctx.send(f"{ctx.author.name}, here is a list of your totals!\n"
                               f"{msg}\nKeep up the **great gains** you're making!")

        else:
            ses.close()
            return

    @commands.command(aliases=["ra", "Ra", "RA", "remove_a", "r_activity"])
    async def remove_activity(self, ctx, exercise):
        """
        Remove ALL activities of a certain name that you've been
        tracking from Gainsworth's memory banks. BEWARE! This will remove all gains
        associated with that activity that you've recorded.
        An example command might look like this: \n
        g!remove_activity Pushups\n\n
        """
        ses, user = await self._check_registered(ctx)
        if user:
            remove_target = ses.query(Exercise).filter(Exercise.user_id == user.id) \
                            .filter(Exercise.name == exercise).delete()
            self.logger.info(f"records deleted: {remove_target}")
            # minus the Exercise made by g!ce
            total_removed = int(str(remove_target)) - 1
            if total_removed < 0:
                total_removed = 0
            ses.commit()
            ses.close()
            await ctx.send(f"{ctx.author.name}, your **{total_removed}** activity"
                           f" records of **{exercise}** were deleted. You can type"
                           " `!list_activities` to see which activities I'm keeping"
                           " track of, or `!help create_activity` to see how you"
                           " start tracking a new one!")
        else:
            ses.close()
            return

    @commands.command()
    async def remove_me_please(self, ctx):
        """
        Ask Gainsworth to purge all information about you in its memory banks.\n
        WARNING: This action is irreversible, and will delete all gains and progress
        associated with you.
        """
        ses, user = await self._check_registered(ctx)
        if user:
            remove_target = ses.query(User).filter(User.id == user.id).delete()
            self.logger.info(f"records deleted: {remove_target}")
            ses.commit()
            ses.close()
            await ctx.send(f"{ctx.author.name}, all records of your activity was"
                           f" removed from my database. If you'd like to start again,"
                           " type `g!help create_activity` to get started."
                           )
        else:
            ses.close()
            return

    @commands.command()
    async def save_my_data(self, ctx):
        """
        This command will set the flag that would normally automatically purge your user
        data after one year to 'False', meaning Gainsworth will store your activity data
        indefinitely.
        """
        ses, user = await self._check_registered(ctx)
        if user:
            change_target = ses.query(User).filter(User.id == user.id).first()
            change_target.auto_remove = False
            self.logger.info(f"auto-remove flag for {change_target} removed")
            ses.commit()
            ses.close()
            await ctx.send(f"{ctx.author.name}, your acitivity data will now be saved"
                           f" until you choose to manually remove it with the"
                           " `g!remove_me_please` command."
                           )
        else:
            ses.close()
            return


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsMemory(client))
