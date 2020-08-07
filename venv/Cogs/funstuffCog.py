from discord.ext import commands
import discord
import AutoPilot
from Cogs import rankingsCog
from Cogs import moderationCog
from systemUtilitys import *
import time


def setup(client):
    client.add_cog(FunStuffModule(client))

class FunStuffModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.modUtility = moderationCog.ModUtilityModule(self.client)
        self.memberdata = rankingsCog.ActivityModule(self.client)
        self.running = True

    def loadguildinfo(self, guildID):
        try:
            stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)].update({'ExtraConfigs':{}})
        stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        return stats

    def saveGuildInfo(self,guildID,info):
        AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs'] = info

    async def findMailChannel(self,prefix):
        guilds = await self.client.fetch_guilds(limit=150).flatten()
        for guild in guilds:
            info = self.loadguildinfo(guild.id)
            try:
                Sprefix = info['Modmail']['ID']
            except KeyError:
                Sprefix = None
            if str(prefix.lower()) == str(Sprefix).lower():
                return guild
        return None

    @commands.command(brief="Creates a vote")
    async def vote(self, context):
        member = context.author
        try:
            vote = str(context.message.content).split(" ", 1)[1]
        except:
            await context.send("Vote must contain a vote")
            return
        embed = discord.Embed(title="", description=str(member.mention) + "'s Query",
                              timestamp=context.message.created_at)
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name="Query", value=str(vote), inline=False)
        embed.set_footer(text="userID: " + str(member.id))
        message = await context.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❓')
        await message.add_reaction('❌')

    @commands.command(brief="Configure Suggestion Channel, Server Mod's only")
    @userIsAuthorized(1)
    async def setSuggestion(self,context):
        guild = context.message.guild
        member = context.message.author
        guildInfo = self.loadguildinfo(guild.id)

        if context.message.channel_mentions:
            targetChannel = context.message.channel_mentions[0]
        else:
            await context.send("This command requires a mentioned channel")
        try:
            message = await targetChannel.send("Perms Test")
            await message.delete()
        except:
            await context.send("Incorrect Permissions")
            return
        guildInfo.update({"SuggestionChannel":targetChannel.id})
        self.saveGuildInfo(guild.id,guildInfo)
        await context.send("Suggestion's Channel Configured")

    @commands.command(help="Allows you to make suggestions in servers with it enabled\nUse -suggestion [suggestion] "
                           "to make a suggestion")
    async def suggestion(self,context):
        guild = context.message.guild
        member = context.message.author
        guildInfo = self.loadguildinfo(guild.id)
        try:
            suggestion = str(context.message.content).split(" ",1)[1]
        except:
            await context.send("Suggestion must contain a suggestion")
            return
        try:
            channelID = guildInfo['SuggestionChannel']
            embed = discord.Embed(title="",description=str(member.mention) + "'s Suggestion",
                                  timestamp=context.message.created_at)
            embed.set_author(name=str(member),icon_url=member.avatar_url)
            embed.add_field(name="Suggestion",value=str(suggestion),inline=False)
            embed.set_footer(text="userID: " + str(member.id))
            channel = self.client.get_channel(int(channelID))
            message = await channel.send(embed=embed)
            await message.add_reaction('✅')
            await message.add_reaction('❓')
            await message.add_reaction('❌')
            await context.message.delete()
        except KeyError:
            await context.send("Suggestion Channel Not Configured")
        pass

    @commands.command(brief="Configure ModMail Channel, Server Mod's only")
    @userIsAuthorized(1)
    async def configModmail(self, context):
        guild = context.message.guild
        extraConfigs = self.loadguildinfo(guild.id)

        if context.message.channel_mentions:
            targetChannel = context.message.channel_mentions[0]
            try:
                prefix = amount = str(context.message.content).split(" ", 2)[2]
            except:
                await context.send("Please include a three letter Acronym for your server")
                return
        else:
            await context.send("This command requires a mentioned channel")
            return
        try:
            message = await targetChannel.send("Perms Test")
            await message.delete()
        except:
            await context.send("Incorrect Permissions")
            return
        if await self.findMailChannel(str(prefix)):
            await context.send("Server Acronym already taken")
            return
        extraConfigs.update({"Modmail": {}})
        extraConfigs['Modmail']['ID'] = str(prefix)
        extraConfigs['Modmail']['channel'] = targetChannel.id
        self.saveGuildInfo(guild.id, extraConfigs)
        await context.send("ModMail Channel Configured")

    @commands.command(name="modmail", aliases=['mail'],brief="Send Mail to moderators of servers",
                      help="Used to send messages to a servers modMail channel"
                                                            "\n---In DM's---\n-modmail [serverID|serverAcronym] your message"
                                                            "\n---In a server---\n-modmail your message")
    async def modmail(self, context):
        guild = context.message.guild
        inDM = False
        if not guild:
            inDM = True
            try:
                address = str(context.message.content).split(" ", 2)[1]
                content = str(context.message.content).split(" ", 2)[2]
            except IndexError:
                await context.send("Plase include both a [serverID|Acryonm] and a message")
                return
            try:
                IDguild = self.client.get_guild(int(address))
                if IDguild:
                    guild = IDguild
                else:
                    await context.send("Invalid Server ID")
                    return
            except:
                guild = await self.findMailChannel(address)
                if not guild:
                    await context.send("No server with that prefix found")
                    return
                guild = self.client.get_guild(int(guild.id))
            member = guild.get_member(context.message.author.id)
            if not member:
                await context.send("You cannot send mail to a server you aren't a member of")
                return
        else:
            member = context.message.author
            try:
                content = str(context.message.content).split(" ", 1)[1]
            except:
                await context.send("Mail must contain mail")
                return

        guildInfo = self.loadguildinfo(guild.id)
        try:
            channelID = guildInfo['Modmail']['channel']
            embed = discord.Embed(title="", description=str(member.mention) + " has sent mail",
                                  timestamp=context.message.created_at)
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            embed.add_field(name="Content", value=str(content), inline=False)
            embed.set_footer(text="userID: " + str(member.id))
            channel = self.client.get_channel(int(channelID))
            message = await channel.send(embed=embed)
            if not inDM:
                await context.message.delete()
                dm  = member.dm_channel
                if not dm:
                    dm = await member.create_dm()
                await dm.send("Success! Your mail has been delivered to " + str(guild))
            else:
                await context.send("Success! Your mail has been delivered to " + str(guild))
        except KeyError:
            await context.send(str(guild) + " has no mail channel configured")
            return

    @commands.command(name="scheduleIconChange", aliases=['planProfileChange'], description=
    "Schedules an icon change up to 6 months out\nIcon= Attach the png you want to be the servers pfp\n"
    "Time= Use the format MM/DD/YY or a Unix Timestamp\nNote: Only one event can be scheduled at a time")
    @userIsAuthorized(1)
    async def scheduleIconChange(self, context):
        guild = context.message.guild
        if context.message.attachments:
            try:
                timeStr = str(context.message.content).split(" ", 1)[1]
                if str(timeStr).find('/') > 0:
                    Ttime = time.mktime(time.strptime(timeStr, '%m/%d/%Y'))
                else:
                    Ttime = timeStr
                if (int(Ttime) < time.time()) or (int(Ttime) > time.time() + 1.577e+7):
                    await context.send("Time is outside of provided timeslot")
                    return
                newIcon = context.message.attachments[0]
            except Exception as e:
                await context.send("Unable to decode provided time: " + str(e))
                return
        else:
            await context.send("Please attach an image to add")
            return

        guildInfo = self.loadguildinfo(guild.id)

        guildInfo['iconChange'] = [Ttime,newIcon.url]

        self.saveGuildInfo(guild.id,guildInfo)

        await context.send("Scheduled Icon change saved!\nTargeted Time: " + time.ctime(int(Ttime)) + "±60s")

    @commands.command()
    @userIsAuthorized(1)
    async def chaos(self, context):
        targetUserchannel = context.message.author.voice.channel
        victemUserchannel = context.message.mentions[0].voice.channel

        for member in victemUserchannel.members:
            await member.move_to(targetUserchannel)
