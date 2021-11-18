from discord.ext import commands


class Example(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents the particular bot that is using the cog.
        """
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global listeners,
        which means you can have multiple cogs listening for the same events and
        taking actions based on those events.
        """
        print("Example extension has been loaded")

    @commands.command()
    async def yoohoo(self, ctx):
        """
        This is a useless example command to demonstrate how commands can be added to
        the cog and then made available to the bot when the cog is loaded.
        I should note here that the command/function's docstring (this text right here)
        will be used by the bot as its "help" and example text by default.
        More information can be found in the discord.py docs or our contributing docs.
        """
        await ctx.send("Yoohoo! This command runs in the Example cog")


def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    client.add_cog(Example(client))
