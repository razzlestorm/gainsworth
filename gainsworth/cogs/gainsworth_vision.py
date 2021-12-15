import logging
import sys

from discord.ext import commands
import pandas as pd
import plotly.express as px

from gainsworth.db.models import Exercise, User


class GainsVision(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents
        the particular bot that is using the cog.
        """
        self.client = client
        self._last_member = None
        self.logger = logging.getLogger(__name__)
        self.logger.info('GainsVision Cog instance created')

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global listeners,
        which means you can have multiple cogs listening for the same events and
        taking actions based on those events.
        """
        print("Gainsworth is ready to visualize your gains!")

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
        elif isinstance(error, ignored):
            return
        else:
            await ctx.send(f'{ctx.author.name}, something went wrong with your input.')

    @commands.command(aliases=["sg", "see_g", "s_gains"])
    async def see_gains(self, ctx, time="week"):
        """
        Use this command to create a visualization of all your gains for the past week,
        month, or year! Just type g!see_gains {week/month/year}, and Gainsworth will
        create a graph that you can download and share with friends!
        An example command might look like this: \n
        g!see_gains month
        """
        memory = self.client.get_cog("GainsMemory")
        if memory is not None:
            ses, user = await memory._check_registered(ctx)
        if user:
            # this successfully gets the df
            exercises = pd.read_sql(ses.query(Exercise).filter(Exercise.user_id == user.id).statement, ses.bind)
            ses.close()
            breakpoint()
            # plotting logic
            fig = px.line(exercises, x="date", y="reps", title="GAINS!")
            # https://github.com/ChattyRS/RuneClock/blob/master/cogs/runescape.py
            # create img file
            # send img
            # remember to close session

        else:
            ses.close()
            return


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsVision(client))
