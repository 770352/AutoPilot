from discord.ext import commands
import discord
import psutil
import AutoPilot
from Cogs import moderationCog, rankingsCog
import time
from itertools import islice


def setup(client):
    client.add_cog(ActionLogModule(client))

class ActionLogModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.modUtility = moderationCog.ModUtilityModule(self.client)
        self.ranking = rankingsCog.ActivityModule(self.client)
        self.ignoreRole = []

    @commands.Cog.listener()
    async def on_ready(self):
        if (AutoPilot.ServerSettings['ProfilesInfo']['LastSaveRaw'] < (time.time() - 900)) or (psutil.boot_time() - time.time() < 500):
            print("Downtime")
            #await self.serviceRestored(AutoPilot.ServerSettings['ProfilesInfo']['LastSaveRaw'])

    async def serviceRestored(self,downStamp,reason='N/A'):
        guilds = await self.client.fetch_guilds(limit=150).flatten()
        for guild in guilds:
            actionLogID = self.getActionChannel(guild.id)
            if actionLogID:
                embed = discord.Embed(title="Service Restored",color=0x11ff00)
                embed.set_author(name=str(self.client.user.name), icon_url=self.client.user.avatar_url, url=AutoPilot.atcInvite)
                #embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.add_field(name="Time of outage", value=str(time.ctime(downStamp)), inline=False)
                embed.set_footer(text="Cause: " + str(reason))
                channel = self.client.get_channel(int(actionLogID))
                await channel.send(embed=embed)

    def getActionChannel(self, guildID):
        try:
            channel = AutoPilot.ServerSettings[str(guildID)]["ServerSettings"]["logChannel"]
            return channel
        except KeyError as e:
            return None

    async def sendLog(self, guildID, embed):
        actionLogID = self.getActionChannel(guildID)
        if actionLogID:
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)

    @commands.command()
    async def Setlogchannel(self,context):
        targetchannel = context.message.channel_mentions[0]
        guild = context.message.guild

        if not self.modUtility.getAPLevel(guild,context.message.author.id) >= 1:
            return
        try:
            await targetchannel.send("Permissions test")
        except:
            await context.send("Incorrect Permissions")
            return
        try:
            AutoPilot.ServerSettings[str(context.message.guild.id)]["ServerSettings"].update({"logChannel": targetchannel.id})
        except KeyError:
            AutoPilot.ServerSettings[str(context.message.guild.id)].update({"ServerSettings":{"logChannel": targetchannel.id}})
        await context.send("AutoLog Channel Configured")

    @commands.Cog.listener()
    async def on_member_update(self,memberB,memberA):
        actionLogID = self.getActionChannel(memberA.guild.id)
        if actionLogID:
            pass
        Sroles = []
        if memberB.roles != memberA.roles:
            for role in memberA.roles:
                Sroles.append(int(role.id))
            self.modUtility.updateUserRoles(memberA.guild.id,memberA.id,Sroles)
            await self.on_member_roleChange(memberB,memberA)
        if memberB.nick != memberA.nick:
            await self.on_member_changeNick(memberB,memberA)

    def Diff(self, li1, li2):
        return (list(set(li1) - set(li2)))

    async def on_member_roleChange(self,memberB,memberA):
        if memberA.id in self.ignoreRole:
            return
        actionLogID = self.getActionChannel(memberA.guild.id)
        if actionLogID:
            removedRoles = self.Diff(memberB.roles,memberA.roles)
            addedRoles = self.Diff(memberA.roles, memberB.roles)
            print(str(removedRoles) + ":" + str(addedRoles))
            embed = discord.Embed(title=str(memberA),
                                  description=str(memberA.mention) + " Roles Changed",
                                  color=0xF0F0FE)
            embed.set_thumbnail(url=memberA.avatar_url)
            embed.set_footer(text="UserID: " + str(memberA.id))
            try:
                newroles = list(addedRoles)
                NroleString = str(newroles[0].mention)
                for role in newroles[1:]:
                    NroleString = str(role.mention) + ", " + NroleString
                embed.add_field(name="New Roles",value=str(NroleString),inline=False)
            except:
                pass
            try:
                oldroles = list(removedRoles)
                OroleString = str(oldroles[0].mention)
                for role in oldroles[1:]:
                    OroleString = str(role.mention) + ", " + OroleString
                embed.add_field(name="Removed Roles", value=str(OroleString), inline=False)
            except:
                pass

            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)

    async def on_member_changeNick(self,memberB,memberA):
        actionLogID = self.getActionChannel(memberA.guild.id)
        if actionLogID:
            embed = discord.Embed(title=str(memberA),
                                  description=str(memberA.mention) + " Changed Their Nickname",
                                  color=0x00FFFF)
            embed.set_thumbnail(url=memberA.avatar_url)
            embed.set_footer(text="UserID: " + str(memberA.id))
            if memberB.nick:
                embed.add_field(name="Orignal",value=str(memberB.nick),inline=False)
                embed.add_field(name="Edited", value=str(memberA.nick), inline=False)
            else:
                embed.add_field(name="Orignal", value="N/A", inline=False)
                embed.add_field(name="Edited", value=str(memberA.nick), inline=False)
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self,payload):
        if payload.cached_message:
            return
        print("Uncached message")
        print(str(payload))
        actionLogID = self.getActionChannel(payload.guild_id)
        guild = self.client.get_guild(int(payload.guild_id))
        Mchannel = self.client.get_channel(int(payload.channel_id))
        if actionLogID:
            embed = discord.Embed(title="Message Deleted",
                                  description="Message Deleted In: " + str(Mchannel.mention),
                                  color=0xFF00FE)
            embed.add_field(name="Message", value="N/A", inline=False)
            embed.set_footer(text="MessageID: " + str(payload.message_id))
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, Message):
        if Message.author.bot:
            return
        actionLogID = self.getActionChannel(Message.guild.id)
        if actionLogID:
            embed = discord.Embed(title=str(Message.author.nick),
                                  description="Message Deleted In: " + str(Message.channel.mention),
                                  color=0xFF00FE, timestamp=Message.created_at)
            embed.set_thumbnail(url=Message.author.avatar_url)
            if Message.content:
                embed.add_field(name="Message", value=str(Message.content), inline=False)
            else:
                embed.add_field(name="Message", value="N/A", inline=False)
            embed.set_footer(text="UserID:" + str(Message.author.id))
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if user.bot:
            return
        actionLogID = self.getActionChannel(guild.id)
        if actionLogID:
            guildID = str(guild.id)
            userID = str(user.id)

            embed = discord.Embed(title="User Banned",
                                  description=str(user) + " Was Banned",
                                  color=0xFF0000)
            embed.set_thumbnail(url=user.avatar_url)
            embed.add_field(name="Account Created", value=str(user.created_at).split(".",1)[0], inline=False)
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)
        pass


    @commands.Cog.listener()
    async def on_member_unban(self,guild, user):
        pass

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if len(messages) < 50:
            messageList = iter(messages)
            length_to_split = [10,10,10,10,10]
            splitList = [list(islice(messageList, elem))for elem in length_to_split]
            for Messages in splitList:
                    try:
                        Message = Messages[0]
                    except IndexError:
                        break
                    if Message.author.bot:
                        return
                    actionLogID = self.getActionChannel(Message.guild.id)
                    if actionLogID:
                        embed = discord.Embed(title="Bulk Message Delete",
                                              description=str(len(messages)) + " Messages Deleted In: " + str(Message.channel.mention),
                                              color=0xFF00FE, timestamp=Message.created_at)
                        #embed.set_thumbnail(url=Message.author.avatar_url)
                        for message in Messages:
                            if message.content:
                                embed.add_field(name=str(message.created_at).split(".",1)[0] + ": " + str(message.author), value=str(message.content), inline=False)
                            else:
                                embed.add_field(name="Message", value="N/A", inline=False)
                        embed.set_footer(text="UserID:" + str(Message.author.id))
                        channel = self.client.get_channel(int(actionLogID))
                        await channel.send(embed=embed)
                        pass
        else:
            Message = messages[0]
            actionLogID = self.getActionChannel(Message.guild.id)
            if actionLogID:
                embed = discord.Embed(title=str(Message.author.nick),
                                      description="Bulk Message Delete In: " + str(Message.channel.mention),
                                      color=0xFF00FE, timestamp=Message.created_at)
                embed.add_field(name="Messages Deleted", value=str(len(messages)), inline=False)
                embed.set_footer(text="ChannelID:" + str(Message.channel.id))
                channel = self.client.get_channel(int(actionLogID))
                await channel.send(embed=embed)
                pass

    @commands.Cog.listener()
    async def on_raw_message_edit(self,payload):
        if payload.cached_message:
            return
        Mchannel = self.client.get_channel(int(payload.channel_id))
        guild = Mchannel.guild
        actionLogID = self.getActionChannel(guild.id)
        if actionLogID:
            try:
                content = payload.data['content']
            except:
                content = None
            try:
                member = payload.data['member']
                author = payload.data['author']
            except:
                return
            guildID = str(guild.id)
            channelID = str(payload.channel_id)
            userID = str(author['id'])
            if (self.client.get_user(int(author['id']))).bot:
                return
            messageID = str(payload.message_id)
            link = "https://discordapp.com/channels/" + str(guildID) + "/" + str(channelID) + "/" + str(messageID)
            avatarLink = "http://cdn.discordapp.com/avatars/" + str(userID) + "/" + author['avatar'] + ".webp?size=1024"
            embed = discord.Embed(title=str(member['nick']),
                                  description="[MESSAGE](" + link + ") Edited In: " +
                                              str(Mchannel.mention), color=0xFF00FE)
            embed.set_thumbnail(url=avatarLink)
            embed.add_field(name="Orignal", value="N/A", inline=False)
            if content:
                embed.add_field(name="Edited", value=str(content), inline=False)
            else:
                embed.add_field(name="Edited", value="N/A", inline=False)
            embed.set_footer(text="UserID: " + str(userID))
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message_edit(self, BeforeMessage, AfterMessage):
        if BeforeMessage.author.bot:
            return
        actionLogID = self.getActionChannel(BeforeMessage.guild.id)
        if actionLogID:
            guildID = str(BeforeMessage.guild.id)
            channelID = str(BeforeMessage.channel.id)
            userID = str(BeforeMessage.author.id)
            messageID = str(BeforeMessage.id)
            if not AfterMessage.edited_at:
                return
            link = "https://discordapp.com/channels/" + str(guildID) + "/" + str(channelID) + "/" + str(messageID)
            embed = discord.Embed(title=str(BeforeMessage.author.nick),description="[MESSAGE](" + link + ") Edited In: " +
                        str(BeforeMessage.channel.mention), color=0xFF00FE,timestamp=AfterMessage.edited_at)
            embed.set_thumbnail(url=AfterMessage.author.avatar_url)
            if BeforeMessage.content:
                embed.add_field(name="Orignal",value=str(BeforeMessage.content),inline=False)
                embed.add_field(name="Edited", value=str(AfterMessage.content), inline=False)
            else:
                embed.add_field(name="Orignal", value="N/A", inline=False)
                embed.add_field(name="Edited", value="N/A", inline=False)
            embed.set_footer(text="UserID:" + str(userID))
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)
            pass

    @commands.Cog.listener()
    async def on_member_join(self, Member):
        if Member.bot:
            return
        self.ignoreRole.append(int(Member.id))
        newMember = False
        guildID = str(Member.guild.id)
        userID = str(Member.id)
        restored, total = await self.modUtility.reassignRoles(Member)
        actionLogID = self.getActionChannel(Member.guild.id)
        self.ranking.loadUserStats(guildID, userID)
        self.modUtility.loadUserPunishments(guildID, userID)
        self.modUtility.getUserInfractions(guildID, userID)

        if actionLogID:
            embed = discord.Embed(title=str(Member),
                                  description="User Joined: " + str(Member.mention),
                                  color=0x00FF00)
            if not newMember:
                embed.description = "User Rejoined: " + str(Member.mention)
            embed.set_thumbnail(url=Member.avatar_url)
            embed.add_field(name="Account Created",value=str(Member.created_at).split(".",1)[0],inline=False)
            embed.add_field(name="Role's Restored",value=str(restored) + "/" + str(total-1))
            channel = self.client.get_channel(int(actionLogID))
            embed.set_footer(text="UserID:" + str(userID))
            await channel.send(embed=embed)
        self.ignoreRole.remove(int(Member.id))
        pass

    @commands.Cog.listener()
    async def on_member_remove(self, Member):
        if Member.bot:
            return
        actionLogID = self.getActionChannel(Member.guild.id)
        if actionLogID:
            guildID = str(Member.guild.id)
            userID = str(Member.id)
            embed = discord.Embed(title=str(Member),
                                  description="User Left: " + str(Member.mention),
                                  color=0xF0C0FE)
            embed.set_thumbnail(url=Member.avatar_url)
            embed.add_field(name="Join Date", value=str(Member.joined_at).split(".",1)[0], inline=False)
            embed.add_field(name="Account Created", value=str(Member.created_at).split(".",1)[0], inline=False)
            embed.set_footer(text="UserID: " + str(userID))
            channel = self.client.get_channel(int(actionLogID))
            await channel.send(embed=embed)
            roles = []
            for role in Member.roles:
                roles.append(int(role.id))
            self.ranking.loadUserStats(guildID, userID)
            self.modUtility.loadUserPunishments(guildID, userID)
            self.modUtility.getUserInfractions(guildID, userID)
            self.modUtility.updateUserRoles(guildID, userID, roles)
        pass

    @commands.Cog.listener()
    async def on_guild_join(self, Guild):
        print("Joined new Guild")
        AutoPilot.ServerSettings.update({str(Guild.id): {}})