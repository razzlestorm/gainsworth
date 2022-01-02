from datetime import datetime, timedelta
import logging
import io
import sys
from typing import List

import discord
from discord.ext import commands
import pandas as pd
import plotly.express as px

from gainsworth.db.models import Exercise


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
        month, or year! Just type g!see_gains {week/month/season/year} {line/histogram},
        and Gainsworth will create a graph that you can download and share with friends!
        An example command might look like this: \n
        g!see_gains month histogram \n
        OR
        g!see_gains (defaults to weekly line graphs)
        """
        TIMES = {
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
        memory = self.client.get_cog("GainsMemory")
        if memory is not None:
            ses, user = await memory._check_registered(ctx)
        if user:
            # this gets the df and filters by time
            exercises = pd.read_sql(ses.query(Exercise)
                                    .filter(Exercise.user_id == user.id)
                                    .statement, ses.bind)
            subset = exercises[exercises['date'] > 
                               (datetime.utcnow() - 
                               timedelta(days=TIMES.get(time, 7)))]
            ses.close()
            subset = subset.set_index('date')
            # create empty df filled with all dates in range
            end = datetime.utcnow()
            start = (end-timedelta(days=TIMES.get(time, 7)))
            dates = pd.date_range(start=start, end=end, freq='D')
            idx_ref = pd.DatetimeIndex(dates)
            idx_df = pd.DataFrame(index=idx_ref)
            subset_exc = pd.merge(idx_df,
                                  subset,
                                  how='outer',
                                  left_index=True,
                                  right_index=True)
            # All of these columns are unneeded for graphing
            subset_exc = subset_exc.drop(["id", "user_id", "unit"], axis=1)

            def add_populated_rows(names: List, df: pd.DataFrame) -> pd.DataFrame:
                for row in df['name'].isna().index:
                    ii = 0
                    for name in names:
                        ii += 1
                        df.loc[row + timedelta(seconds=ii)] = [name, 0.0]
                df = df.dropna(subset=['name'])
                return df

            exc_names = [n for n in subset_exc['name'].unique() if isinstance(n, str)]
            subset_exc = add_populated_rows(exc_names, subset_exc)
            # plotting logic
            # see templates: https://plotly.com/python/templates/#theming-and-templates
            if plot_type in ["hist", "histogram", "h", "his", "hgram"]:
                get_max = subset_exc.groupby([pd.Grouper(freq='D'), "name"]) \
                          .sum().reset_index(level="name")
                fig = px.histogram(subset_exc,
                                   x=subset_exc.index,
                                   y="reps",
                                   color="name",
                                   labels={
                                           "date": "Date",
                                           "reps": "No. of Reps",
                                           "name": "Exercises:"
                                          },
                                   title="GAINS!",
                                   template="plotly_dark+xgridoff",
                                   nbins=TIMES.get(time, 7),
                                   barmode="group"
                                   )
                max_val = get_max["reps"].max()
                fig.update_layout(yaxis={"range": [0, max_val + max_val/10]})
            else:
                subset_exc = subset_exc.groupby([pd.Grouper(freq='D'), "name"]) \
                             .sum().reset_index(level="name")
                fig = px.line(subset_exc,
                              x=subset_exc.index,
                              y="reps",
                              color="name",
                              labels={
                                      "index": "Date",
                                      "date": "Date",
                                      "reps": "Daily No. of Cumulative Reps",
                                      "name": "Exercises:"
                                     },
                              title="GAINS!",
                              template="plotly_dark+xgridoff",
                              )
                fig.update_traces(mode="markers+lines")
                max_val = subset_exc["reps"].max()
                fig.update_layout(yaxis={"range": [0, max_val + max_val/10]})
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
