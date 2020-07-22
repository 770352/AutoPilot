from discord.ext import commands
import discord
import asyncio
import AutoPilot
from Cogs import actionLogCog, rankingsCog, moderationCog
import time, shutil, requests

def setup(client):
    client.add_cog(AntiRaidModule(client))

class AntiRaidModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.modUtility = moderationCog.ModUtilityModule(self.client)

    @commands.Command
    async def purgeInvites(self, context):
        guild = context.message.guild
        if not self.modUtility.getAPLevel(guild, context.message.author.id) >= 1:
            return

        invites = await guild.invites()

        await context.send("Purging all invites")

        for invite in invites:
            try:
                await invite.delete(reason="Server Lockdown")
            except:
                await context.send("Unable to delete invite: " + str(invite.code))

        await context.send("Action Completed")