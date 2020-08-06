from discord.ext import commands
import discord
import psutil
import AutoPilot
import asyncio


class utilitys():
    def __init__(self, client):
        self.client = client

    def getMessageTemplate(self, guildID, msgType):
        try:
            return AutoPilot.ServerSettings[str(guildID)]["ServerSettings"]['Templates'][str(msgType)]
        except KeyError:
            return None

    def setMessageTemplate(self, guildID, msgType, template):
        try:
            AutoPilot.ServerSettings[str(guildID)]["ServerSettings"]['Templates'][str(msgType)] = template
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)]["ServerSettings"]['Templates'] = {str(msgType): str(template)}

    async def generateWelcomeJoin(self, guild, member):
        template = self.getMessageTemplate(guild.id, 'welcomeJoin')
        if template:
            formated = str(template).format(server=guild.name, memberMention=member.mention,
                                            memberName=member.display_name, member=str(member))
            return formated
        else:
            return None

    async def generateWelcomeLeave(self, guild, member):
        template = self.getMessageTemplate(guild.id, 'welcomeLeave')
        if template:
            formated = str(template).format(server=guild.name, memberMention=member.mention,
                                            memberName=member.display_name, member=str(member))
            return formated
        else:
            return None
