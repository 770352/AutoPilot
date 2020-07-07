from discord.ext import commands
import discord
import inspect
import AutoPilot, systemUtilitys
from Cogs import rankingsCog
from Cogs import moderationCog
import time, asyncio


def setup(client):
    client.add_cog(HelpGenerator(client))


class HelpGenerator(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(name='help', aliases=['about'], brief='Creates this message',
                      description='Created a embed with all bot commands')
    async def customHelp(self, context, targetedCommand=None):
        if targetedCommand:
            await self.singleCommandHelp(context, targetedCommand)
        else:
            await self.createHelpPages(context)

    async def singleCommandHelp(self, context, targetedCommand):
        loadedCommands = self.client.commands
        clientName = (context.message.guild.get_member(int(self.client.user.id))).nick
        embed = discord.Embed(title=str(clientName) + " Help", description="Command: " + targetedCommand)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        command = None
        for Rcommand in loadedCommands:
            if str(Rcommand.name).lower() == str(targetedCommand).lower():
                command = Rcommand
                break
        if command:
            embed.add_field(name='Description', value=command.description, inline=False)
            embed.add_field(name="Aliases", value=command.aliases if len(command.aliases) > 0 else "None", inline=False)
            embed.add_field(name="Host Module", value=command.cog.qualified_name)
            embed.set_footer(text="Could Execute Here? " + ("No" if False in command.checks else "Yes"))
        else:
            embed.add_field(name='Command Not Found', value='Please make sure you spell the command correctly')
        await context.send(embed=embed)

    async def createHelpPages(self,context):
        loadedModules = self.client.cogs
        pages = []
        clientName = (context.message.guild.get_member(int(self.client.user.id))).nick
        perPage = 6
        for cog in loadedModules.values():
            onPage = 0
            embed = discord.Embed(title="Module: " + cog.qualified_name)
            embed.set_thumbnail(url=self.client.user.avatar_url)
            for command in cog.get_commands():
                if onPage < perPage:
                    embed.add_field(name=str(context.prefix) + str(command.name), value=
                    command.brief if command.brief else (str(command.description).split('\n',1)[0])
                    if len(command.description) > 0 else "None",inline=False)
                    onPage += 1
                else:
                    pages.append(embed)
                    onPage = 0
                    embed = discord.Embed(title="Module: " + cog.qualified_name)
                    embed.set_thumbnail(url=self.client.user.avatar_url)
                    embed.add_field(name=str(context.prefix) + str(command.name), value=
                    command.brief if command.brief else (str(command.description).split('\n', 1)[0])
                    if len(command.description) > 0 else "None", inline=False)
            pages.append(embed)
        await self.createInteractiveHelp(context, pages)

    async def createInteractiveHelp(self, context, pages):
        currentPage = 0
        message = None
        embed = None
        active = True
        while active:
            embed = pages[currentPage].set_footer(text="Page: " + str(currentPage + 1) + "/" + str(len(pages)))
            if message:
                await message.edit(embed=embed)
            else:
                message = await context.send(embed=embed)
            #await message.clear_reactions()
            reacts = ["⏮️", "⏪", "⏹️", "⏩", "⏭️"]
            for react in reacts:
                await message.add_reaction(react)

            def check(reaction, user):
                return user == context.message.author and reaction.emoji in reacts

            try:
                react, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
            except asyncio.TimeoutError:
                print("Timeout")
                active = False

            if str(react) == reacts[0]:
                currentPage = 0
                await message.remove_reaction(reacts[0], context.message.author)
            elif str(react) == reacts[1]:
                currentPage -= 1
                await message.remove_reaction(reacts[1], context.message.author)
            elif str(react) == reacts[2]:
                active = False
                await message.remove_reaction(reacts[2], context.message.author)
            elif str(react) == reacts[3]:
                currentPage += 1
                await message.remove_reaction(reacts[3], context.message.author)
            elif str(react) == reacts[4]:
                currentPage = len(pages) - 1
                await message.remove_reaction(reacts[4], context.message.author)
            else:
                active = False

            if currentPage >= len(pages):
                currentPage = 0

            if currentPage < 0:
                currentPage = len(pages) - 1

        await message.clear_reactions()

