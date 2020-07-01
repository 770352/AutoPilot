from discord.ext import commands
import discord
import AutoPilot
from Cogs import rankingsCog
from Cogs import moderationCog


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

    @commands.command()
    async def setSuggestion(self,context):
        guild = context.message.guild
        member = context.message.author
        if not self.modUtility.getAPLevel(guild,context.message.author.id) > 1:
            return
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

    @commands.command()
    async def configModmail(self, context):
        guild = context.message.guild
        if not self.modUtility.getAPLevel(guild, context.message.author.id) > 2:
            return
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

    @commands.command(name="modmail", aliases=['mail'],help="Used to send messages to a servers modMail channel"
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


