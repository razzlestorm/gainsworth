from datetime import datetime, timedelta
import logging
import io
import sys

import discord
from discord.ext import commands
import numpy as np
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
    async def see_gains(self, ctx, time="week", plot_type="line"):
        """
        Use this command to create a visualization of all your gains for the past week,
        month, or year! Just type g!see_gains {week/month/year} {line/histogram}, and 
        Gainsworth will create a graph that you can download and share with friends!
        An example command might look like this: \n
        g!see_gains month histogram \n
        OR 
        g!see_gains (defaults to weekly line graphs)
        """
        TIMES = {
            "week": 7,
            "month": 30,
            "year": 365
        }
        memory = self.client.get_cog("GainsMemory")
        if memory is not None:
            ses, user = await memory._check_registered(ctx)
        if user:
            # this gets the df and filters by time
            exercises = pd.read_sql(ses.query(Exercise).filter(Exercise.user_id == user.id).statement, ses.bind)
            subset = exercises[exercises['date'] > (datetime.utcnow() - timedelta(days=TIMES.get(time, 7)))]
            ses.close()
            subset = subset.set_index('date')

            # create empty df filled with all dates in range
            end = datetime.utcnow().date()
            start = (end-timedelta(days=TIMES.get(time, 7)))
            dates = pd.date_range(start=start, end=end, freq='D')
            idx_ref = pd.DatetimeIndex(dates)
            idx_df = pd.DataFrame(index=idx_ref)
            subset_exc = pd.merge(idx_df, subset, how='outer', left_index=True, right_index=True)

            # This is necessary because if the color parameter sees a NaN it panics
            subset_exc['name'] = subset_exc['name'].fillna("")
            # plotting logic
            # see templates: https://plotly.com/python/templates/#theming-and-templates
            if plot_type in ["hist", "histogram", "h", "his", "hgram"]:
                fig = px.histogram(subset_exc,
                            x=subset_exc.index,
                            y="reps",
                            color="name",
                            labels = {
                                "date": "Date",
                                "reps": "No. of Reps",
                                "name": "Exercises:"
                            },
                            title="GAINS!",
                            template="plotly_dark+xgridoff",
                            nbins=TIMES.get(time, 7),
                            barmode="group"
                            )
            else:
                fig = px.line(subset_exc,
                            x=subset_exc.index,
                            y="reps",
                            color="name",
                            labels = {
                                "date": "Date",
                                "reps": "No. of Reps",
                                "name": "Exercises:"
                            },
                            title="GAINS!",
                            template="plotly_dark+xgridoff",
                            )
                fig.update_traces(mode="markers+lines")
                fig.update_layout(yaxis={"range":[0, subset_exc["reps"].max()]})
            fig.write_image("exercises.png")
            with open("exercises.png", "rb") as f:
                file = io.BytesIO(f.read())
            image = discord.File(file, filename="d_exercises.png")
            await ctx.send(file=image)


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(GainsVision(client))
