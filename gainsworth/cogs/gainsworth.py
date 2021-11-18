from discord.ext import commands
import re


class Gainsworth(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents the particular bot that is using the cog.
        """
        self.client = client
        self._last_member = None

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global listeners,
        which means you can have multiple cogs listening for the same events and
        taking actions based on those events.
        """
        print("Gainsworth is ready to PUMP YOU UP!")


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

def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(Gainsworth(client))
