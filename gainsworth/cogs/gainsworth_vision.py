from datetime import datetime, timedelta
import logging
import io
from typing import List, Literal

import discord
from discord import app_commands
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

    async def _parse_filter(self, exc_names, show):
        """
        This should handle parsing of any args passed into the see_gains command
        and return them in a predetermined order, or return None if they are not
        present or are incorrectly formatted. This assumes default behavior 
        is to query a user's unfiltered weekly line plot.
        """
        filtered_exc = None
        if show:
            filtered_exc = [e.strip(", ") for e in show.split(" ")]
            filtered_exc = [e for e in filtered_exc if e in exc_names]
        # then check that time and plot_type aren't None
        if not filtered_exc:
            activity_filter = None
        else:
            activity_filter = filtered_exc
        return activity_filter

    @app_commands.command()
    async def see_gains(
        self, 
        interaction: discord.Interaction, 
        days: int=7, 
        plot_type: Literal['line', 'histogram'] = 'line',
        show: str=''
        ):
        """
        Create a visualization of all your gains for the past X days! 
        Just type /see_gains {day/week/month/season/year/any number} 
        {line/histogram} {show: activity_name1, activity_name2}, and Gainsworth will 
        create a graph that you can download and share with friends!\n
        An example command might look like this: \n
        /see_gains month histogram \n
        OR\n
        /see_gains (defaults to weekly line graphs)\n
        OR EVEN:\n
        /see_gains week line show: Jogging Pushups\n
        Use the word "show:" to only show certain activities! 
        """
        await interaction.response.defer(thinking=True)
        memory = self.client.get_cog("GainsMemory")
        if memory is not None:
            ses, user = await memory._check_registered(interaction)
        if user:
            exercises = pd.read_sql(ses.query(Exercise)
                                    .filter(Exercise.user_id == user.id)
                                    .statement, ses.bind)
            exc_names = exercises.name.unique()
            activity_filter = await self._parse_filter(exc_names, show)
            if isinstance(days, str):
                try:
                    days = int(days)
                except ValueError:
                    try:
                        days = float(days)
                    except ValueError:
                        await interaction.followup.send("There was a problem with your days, please input a whole number!")
            if not activity_filter:
                # this creates the df and filters by time
                subset = exercises[exercises['date'] >
                                (datetime.utcnow() -
                                timedelta(days=days))]
            else:
                # filters by exercise name
                subset = exercises[exercises['date'] >
                                (datetime.utcnow() -
                                timedelta(days=days))]
                mask = subset['name'].isin(activity_filter)
                subset = subset[mask]
            ses.close()
            subset = subset.set_index('date')
            # create empty df filled with all dates in range
            end = datetime.utcnow()
            start = (end-timedelta(days=days))
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
            # separate these out into different functions
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
                                           "name": "Activities:"
                                          },
                                   title="GAINS!",
                                   template="plotly_dark+xgridoff",
                                   nbins=days,
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
                                      "name": "Activities:"
                                     },
                              title="GAINS!",
                              template="plotly_dark+xgridoff",
                              )
                fig.update_traces(mode="markers+lines", marker={"opacity": 0.5})
                max_val = subset_exc["reps"].max()
                fig.update_layout(yaxis={"range": [0, max_val + max_val/10]})
            fig.write_image("activities.png")
            with open("activities.png", "rb") as f:
                file = io.BytesIO(f.read())
            image = discord.File(file, filename="discord_activities.png")
            await interaction.followup.send(file=image)

async def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    await client.add_cog(GainsVision(client))
