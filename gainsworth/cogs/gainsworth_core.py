import json
import logging
from os.path import exists
import pathlib
import re
import sys
import discord
from discord import app_commands
from discord.ext import commands

from discord.ext.commands import Context, Greedy
from typing import Literal, Optional


class Gainsworth(commands.Cog):
    def __init__(self, client):
        """
        The init function will always take a client, which represents
         the particular bot that is using the cog.
        """
        with open(pathlib.Path("gainsworth", "cfg", "gains_config.json")) as conf:
            self.version = json.load(conf)["version"]
        self.client = client
        self._last_member = None
        self.logger = logging.getLogger(__name__)
        self.logger.info('Gainsworth Cog instance created')

    async def check_changelog(self):
        """
        Checks the version at the top of the changelog. Returns the new version number
        and text of that changelog.
        """
        log_path = pathlib.Path("gainsworth", "cfg", "changelog.md")
        if not exists(log_path):
            return None
        with open(log_path, "r") as file:
            changelog = file.readlines()
        text = ""
        add = False
        for line in changelog:
            if add and re.search("##\s\d\.\d\.\d" , line):
                break
            elif not add and re.search("##\s\d\.\d\.\d", line):
                add = True
                text += line
            elif not add:
                continue
            else:
                text += line
        version = text.split("\n")[0].split(" ")[1]
        return version, text

    async def broadcast_changelog(self, text, filter_name=None):
        """
        Broadcast most recent changes to all servers in the first channel that
        Gainsworth has permission to speak in, across all servers.
        """
        if filter_name:
            guilds = [x for x in self.client.guilds if x.name==filter_name]
        else:
            guilds = self.client.guilds
        for guild in guilds:
            for channel in guild.channels:
                try:
                    await channel.send(text)
                    await channel.send("If you'd like to stop receiving this changelog, please create an issue on my `g!github`") 
                    print(f"changelog sent to {guild.name}: {channel.name}")
                    break
                except Exception:
                    continue
                else:
                    break
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Any listeners you add will be effectively merged with the global
         listeners, which means you can have multiple cogs listening for the
        same events and taking actions based on those events.
        """
        print("Gainsworth is ready to PUMP YOU UP!")
        print(f"Gainsworth is in {len(self.client.guilds)} guilds!")
        version, text = await self.check_changelog()
        if self.version != version:
            self.version = version
            # update config with version
            with open(pathlib.Path("gainsworth", "cfg", "gains_config.json"), "r") as conf:
                config = json.load(conf)
                conf_version = config['version']
                config['version'] = self.version
            with open(pathlib.Path("gainsworth", "cfg", "gains_config.json"), "w") as conf:
                json.dump(config, conf)
                # checking for semi-major version changes
            if version.split(".")[1] != conf_version.split(".")[1]:
                # broadcast changes
                await self.broadcast_changelog(text)


    @commands.Cog.listener()
    async def on_command_error(self, interaction: discord.Interaction, error: discord.InteractionMessage) -> None:
        sys.stdout.write("Command Error: ")
        sys.stdout.write(f"{error}")
        ignored = (commands.CommandInvokeError)
        if isinstance(error, commands.CommandNotFound):
            await interaction.response.send_message(f'{interaction.user.name}, I did not understand that command.'
                           ' Try typing `g!help` to see a list of available commands.')
        # elif isinstance(error, commands.errors.MissingRequiredArgument):
        #     await interaction.response.send_message(f'{interaction.user.name}, there was an issue with that command,'
        #                    f' type `g!help {ctx.args[1].command.name}` to learn more'
        #                    ' about how to format that command')
        # elif isinstance(error, commands.ArgumentParsingError):
        #     await interaction.response.send_message(f'{interaction.user.name}, there was an issue with your arguments,'
        #                    f' type `g!help {ctx.args[1].command.name}` to learn more'
        #                    ' about how to format that command')
        # It's probably better to handle these errors in their respective methods
        elif "'NoneType' object has no attribute 'reps'" in str(error):
            await interaction.response.send_message(f"I didn't find that activity, {interaction.user.name}!"
                           " Type `g!list_activities` to see all the activities I'm"
                           " currently tracking.")
        elif "'NoneType' object has no attribute 'user_id'" in str(error):
            await interaction.response.send_message(f"It looks like you haven't started tracking any activities"
                           f", {interaction.user.name}. Type g!create_activity to get started!")
        elif "duplicate key" in str(error):
            await interaction.response.send_message(f'That activity already exists for you, {interaction.user.name}!'
                           ' Type `g!list_activities` to see all the activities you have'
                           ' already added.')
        elif "UnmappedInstanceError" in str(error):
            await interaction.response.send_message(f"I didn't find that activity, {interaction.user.name}!"
                           " Type `g!list_activities` to see all the activities I'm"
                           " currently tracking.")
        elif isinstance(error, ignored):
            return
        else:
            await interaction.response.send_message(f'{interaction.user.name}, something went wrong with your input.')

    @commands.command(aliases=["sync"])
    @commands.is_owner() #will raise an error if the person who executed the command is not the owner of the bot
    async def sync_command(self, ctx):
        await self.client.tree.sync(guild = discord.Object(id=740310401001980036))
        await ctx.reply("Synced!")
        print("Synced!")


    @app_commands.command()
    async def hello(self, interaction: discord.Interaction) -> None:
        """Says hello"""
        print("message received")
        if interaction.user == self.client.user:
            return
        member = interaction.user
        if self._last_member is None or self._last_member.id != member.id:
            # {0.name} here comes from the MessageEmbed class's "fields" attr
            await interaction.response.send_message('Hello {0.name}~'.format(member))
        else:
            await interaction.response.send_message('Hello {0.name}... Are you getting \
                            your GAINS in?'.format(member))
        self._last_member = member

    @app_commands.command()
    async def github(self, interaction: discord.Interaction) -> None:
        """Display link to the GitHub, so you can read or contribute to my code!"""
        embed = discord.Embed()
        embed.description = (
                            "My code is available to peruse and contribute to on"
                            " [GitHub](https://github.com/razzlestorm/gainsworth). You"
                            " can also visit my "
                            "[Discussions Page]"
                            "(https://github.com/razzlestorm/gainsworth/discussions)"
                            " to make suggestions, flesh out ideas, or show off how"
                            " I'm working in your server!"
                            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def invite(self, interaction: discord.Interaction) -> None:
        """Display the link to invite Gainsworth to your own Discord!"""
        embed = discord.Embed()
        embed.description = (
                             "You can use this [invite link](https://discord.com/api/"
                             "oauth2/authorize?client_id=910743103785271356"
                             "&permissions=309237648448&scope=bot) to invite me"
                             " to your Discord server! Be sure to set my permissions to"
                             " limit me to the channels you would like me to be in!"
        )
        await interaction.response.send_message(embed=embed)

async def setup(client):
    """
    This setup function must exist in every cog file and will ultimately have a
    nearly identical signature and logic to what you're seeing here.
    It's ultimately what loads the Cog into the bot.
    """
    await client.add_cog(Gainsworth(client))
