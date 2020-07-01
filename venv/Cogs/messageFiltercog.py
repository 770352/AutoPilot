from discord.ext import commands
import asyncio
import wordfilter
import AutoPilot
from Cogs import rankingsCog
from Cogs import moderationCog


def setup(client):
    client.add_cog(FilterModule(client))

class FilterModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.modUtility = moderationCog.ModUtilityModule(self.client)
        self.memberdata = rankingsCog.ActivityModule(self.client)
        self.running = True
        wordfilter.clear_list()
        wordfilter.add_words(["fuck","shit", "cock", "pussy", "nigga", "nigger", "cunt", "fag"])

    def loadguildinfo(self, guildID):
        try:
            stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)].update({'ExtraConfigs':{}})
        stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        return stats

    def saveGuildInfo(self,guildID,info):
        AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs'] = info

    @commands.command()
    async def toggleFilter(self,context):
        guild = context.message.guild
        member = context.message.author

        if not self.modUtility.getAPLevel(guild,context.message.author.id) >= 1:
            return

        configs = self.loadguildinfo(guild.id)
        try:
            currentState = configs["filterEnabled"]
        except KeyError:
            currentState = False
        currentState = not currentState
        configs['filterEnabled'] = currentState
        self.saveGuildInfo(guild.id, configs)
        await context.send("Filter State: " + str(currentState))


    @commands.Cog.listener()
    async def on_message(self,message):
        try:
            guild = message.guild
            member = message.author
            configs = self.loadguildinfo(guild.id)
        except:
            return
        try:
            currentState = configs["filterEnabled"]
        except KeyError:
            currentState = False
        if not currentState:
            return
        isbadWord = wordfilter.blacklisted(str(message.content))
        if isbadWord:
            await message.delete()
            channel = message.channel
            warning = await channel.send(str(member.mention) + " watch your language!")
            await asyncio.sleep(5)
            await warning.delete()