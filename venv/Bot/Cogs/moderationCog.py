from discord.ext import commands
import discord
import asyncio
from Bot import AutoPilot
from Bot.Cogs import actionLogCog
import time

isCog = True
isEnabled = True

def setup(client):
    client.add_cog(ModUtilityModule(client))
    client.add_cog(ModerationModule(client))

class ModUtilityModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.running = True

    @commands.Cog.listener()
    async def on_ready(self):
        self.client.loop.create_task(self.timeChecks())

    def loadguildinfo(self, guildID):
        try:
            stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)].update({'ExtraConfigs':{}})
        stats = AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs']
        return stats

    def saveGuildInfo(self,guildID,info):
        AutoPilot.ServerSettings[str(guildID)]['ExtraConfigs'] = info

    def readUserRoles(self,guildID,userID):
        try:
            return AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["Roles"]
        except:
            return None
        
    def updateUserRoles(self,guildID,userID,roles):
        AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)].update({"Roles": roles})

    def getUserInfractions(self,guildID,userID):
        try:
            return AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["RapSheet"]
        except KeyError as e:
            AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)].update({"RapSheet":{
                "Mutes":0,"Warnings":0,"Kicks":0
            }})
            AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)].update({"PunishmentSheet":{
                "UnmuteTime":0,"UnbanTime":0
            }})
            return AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["RapSheet"]
            pass

    def loadCheckList(self, guildID):
        try:
            checkList = AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["TimeChecks"]
            role = AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["MuteRoleID"]
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)].update({"PunishmentData": {
                "TimeChecks": [], "MuteRoleID": 0
            }})
            checkList = AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["TimeChecks"]
            role = AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["MuteRoleID"]
        return (checkList, role)

    def saveCheckList(self,guildID,checklist):
        AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["TimeChecks"] = checklist

    def saveMuteRole(self,guildID,muteRoleID):
        AutoPilot.ServerSettings[str(guildID)]["PunishmentData"]["MuteRoleID"] = muteRoleID

    def loadUserPunishments(self, guildID, userID):
        try:
            table = AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["PunishmentSheet"]
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)].update({"PunishmentSheet": {
                "UnmuteTime": 0, "UnbanTime": 0
            }})
            table = AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["PunishmentSheet"]
        return table

    def saveUserPunishments(self,guildID, userID,mute=None,ban=None):
        self.loadUserPunishments(guildID,userID)
        if mute:
            AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["PunishmentSheet"]["UnmuteTime"] = mute
        if ban:
            AutoPilot.ServerSettings[str(guildID)]["ActivityTable"][str(userID)]["PunishmentSheet"]["UnbanTime"] = ban

    async def timeChecks(self):
        print("Punishment Check Cycle Started")
        while self.running:
            guilds = await self.client.fetch_guilds(limit=150).flatten()
            for guild in guilds:
                checkList, muteRole = self.loadCheckList(guild.id)
                for user in checkList:
                    punishments = self.loadUserPunishments(guild.id, user)
                    unMuteTime = punishments["UnmuteTime"]
                    unBanTime = punishments["UnbanTime"]
                    if unMuteTime < time.time() and unMuteTime != 0:
                        guild = self.client.get_guild(int(guild.id))
                        role = guild.get_role(int(muteRole))
                        member = guild.get_member(int(user))
                        await self.removeRole(member,role)
                        checkList.remove(int(user))
                        self.saveCheckList(guild.id,checkList)
                        self.saveUserPunishments(guild.id,user,mute=0)
                        pass
                    if unBanTime < time.time() and unBanTime != 0:
                        print("Punishment Expired")
                        pass
            await asyncio.sleep(60)


    def getAPLevel(self,guild,userID):

        if str(userID) in AutoPilot.trusted:
            return 4
        elif userID == guild.owner_id:
            return 3
        elif self.isAdmin(guild.id,userID):
            return 2
        elif self.isMod(guild.id,userID):
            return 1
        else:
            return 0

    def isAdmin(self,guildID,userID):
        try:
            return int(userID) in AutoPilot.ServerSettings[str(guildID)]["ServerStaff"]["Admins"]
        except KeyError:
            return False

    def isMod(self,guildID,userID):
        try:
            return int(userID) in AutoPilot.ServerSettings[str(guildID)]["ServerStaff"]["Mods"]
        except KeyError:
            return False

    async def banMember(self,user,guild):
        await guild.ban(user, reason=None, delete_message_days=7)

    async def unBanMember(self,user,guild):
        await guild.unban(user, reason=None)

    async def reassignRoles(self,member):
        guild = member.guild
        userID = member.id

        userRoles = self.readUserRoles(guild.id,userID)
        if userRoles:
            restored = 0
            print(str(userRoles))
            for roleID in userRoles[1:]:
                try:
                    role = guild.get_role(int(roleID))
                    await self.giveRole(member,role)
                    restored += 1
                except Exception as e:
                    print(str(e))
            return (restored, len(userRoles))
        else:
            return (0, 1)


    async def giveRole(self,member,role):
        roles = member.roles
        roles.append(role)
        await member.edit(roles=roles)

    async def removeRole(self,member,role):
        roles = member.roles
        try:
            roles.remove(role)
        except ValueError:
            pass
        await member.edit(roles=roles)

    def calculateEpochTime(self,Ptime):
        seconds_per_unit = {"m": 60, "h": 3600, "d": 86400, "w": 604800,"y":3.154e+7}
        try:
            return int(Ptime[:-1]) * seconds_per_unit[Ptime[-1]]
        except:
            return False

    async def addTimeInfraction(self,context,user,type,Ptime):
        guild = context.message.guild
        checklist, muteRoleID = self.loadCheckList(guild.id)
        if muteRoleID == 0:
            await context.send("This server has no mute role, please assign a mute role to use the mute command")
            return False
        timeDelta = self.calculateEpochTime(Ptime)
        if not timeDelta:
            await context.send("Invalid Time Unit")
            return False
        timeRelease = round(time.time() + abs(timeDelta))
        if type is 'mute':
            muteRole = guild.get_role(int(muteRoleID))
            checklist.append(int(user.id))
            self.saveCheckList(guild.id,checklist)
            self.saveUserPunishments(guild.id, int(user.id), mute=timeRelease)
            await self.giveRole(user,muteRole)
            return True
        if type is 'ban':
            checklist.append(int(user.id))
            self.saveCheckList(guild.id, checklist)
            self.saveUserPunishments(guild.id, int(user.id), ban=timeRelease)
            await self.banMember(user,guild)


    async def getMentionedUser(self,context):
        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ",1)[1]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return False
            except IndexError:
                return False
        else:
            user = context.message.mentions[0]

        return user

    @commands.command()
    async def addMuteRole(self,context):
        roles = context.message.role_mentions
        guild = context.message.guild
        if not self.getAPLevel(guild,context.message.author.id) > 1:
            return
        if roles:
            role = roles[0]
            self.saveMuteRole(guild.id,role.id)
            await context.send("Mute Role Added")
        else:
            await context.send("A role is required to be added")

    @commands.command()
    async def addMod(self, context):

        mod = await self.getMentionedUser(context)
        guild = context.message.guild

        if not self.getAPLevel(guild.id, context.message.author.id) >= 2:
            return

        try:
            AutoPilot.ServerSettings[str(guild.id)]["ServerStaff"]["Mods"].append(int(mod.id))
        except KeyError:
            try:
                AutoPilot.ServerSettings[str(guild.id)]["ServerStaff"].update({"Mods":[int(mod.id)]})
            except KeyError:
                AutoPilot.ServerSettings[str(guild.id)].update({"ServerStaff":{"Mods": [int(mod.id)]}})

        await context.send(str(mod) + " Added To Mod Team")
        pass

    @commands.command()
    async def addAdmin(self, context):

        admin = await self.getMentionedUser(context)
        guild = context.message.guild

        if not self.getAPLevel(guild, context.message.author.id) > 2:
            return

        try:
            AutoPilot.ServerSettings[str(guild.id)]["ServerStaff"]["Admins"].append(int(admin.id))
        except KeyError:
            AutoPilot.ServerSettings[str(guild.id)]["ServerStaff"].update({"Admins":[int(admin.id)]})
        pass

    @commands.command()
    async def delMod(self, context):

        guild = context.message.guild
        pass

    @commands.command()
    async def delAdmin(self, context):

        guild = context.message.guild
        pass




class ModerationModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.utility = AnModUtilityModule(self.client)
        self.log = actionLogCog.AnActionLogModule(self.client)



    @commands.command(name="purge",description="Bulk Deletes Messages From a Channel \n[userID|amount]")
    async def bulkdelete(self,context):
        guild = context.message.guild
        channel = context.message.channel
        target = None
        if not self.utility.getAPLevel(guild, context.message.author.id) >= 1:
            return

        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ",2)[1]
                amount = amount = str(context.message.content).split(" ",2)[2]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                amount = str(context.message.content).split(" ", 1)[1]
                target = False
        else:
            try:
                user = context.message.mentions[0]
                amount = str(context.message.content).split(" ", 2)[2]
            except IndexError:
                amount = 100


        def is_targeted_user(message):
            if target == False:
                return True
            else:
                return message.author == user

        await context.message.delete()

        await channel.purge(limit=int(amount),check=is_targeted_user)


    @commands.command(name="mute",description="")
    async def muteUser(self, context):
        guild = context.message.guild

        if not self.utility.getAPLevel(guild,context.message.author.id) >= 1:
            return

        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ",2)[1]
                time = str(context.message.content).split(" ",2)[2]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                await context.send("Command Requires A Targeted User")
        else:
            try:
                user = context.message.mentions[0]
                time = str(context.message.content).split(" ", 2)[2]
            except IndexError:
                await context.send("Please add the time the user will be muted for, and the reason for the mute")
                return

        if await self.utility.addTimeInfraction(context,user,'mute',time):
            await context.send(str(user) + " Was muted")
            embed = discord.Embed(title=str(user.nick) + " was Muted",color=0xF0F000,description=str(user.mention)
                                  ,timestamp=context.message.created_at)
            await self.log.sendLog(guild.id,embed)

    @commands.command(name="tempBan")
    async def tempban(self,context):
        guild = context.message.guild

        if not self.utility.getAPLevel(guild, context.message.author.id) >= 1:
            return

        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ", 2)[1]
                time = str(context.message.content).split(" ", 2)[2]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                await context.send("Command Requires A Targeted User")
        else:
            try:
                user = context.message.mentions[0]
                time = str(context.message.content).split(" ", 2)[2]
            except IndexError:
                await context.send("Please add the time the user will be banned for, and the reason for the ban")
                return

        if await self.utility.addTimeInfraction(context,user,'ban',time):
            await context.send(str(user) + " Was Temporaly Nanned")
            embed = discord.Embed(title=str(user.nick) + " Was TempBanned",color=0xFFF000,description=str(user.mention)
                                  ,timestamp=context.message.created_at)
            await self.log.sendLog(guild.id,embed)

    @commands.command(help="Returns an embed with userinfo")
    async def userinfo(self, context):

        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ",1)[1]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                user = context.message.author
        else:
            user = context.message.mentions[0]

        guildID = context.message.guild.id
        guild = context.message.guild
        status = str(user.status).upper()
        if status == "OFFLINE":
            try:
                lastonline = time.ctime(
                    AutoPilot.ServerSettings[str(guildID)]['ActivityTable'][str(user.id)]["RecentStats"]["lastMsgTime"])
            except KeyError:
                lastonline = "N/A"
        else:
            lastonline = "Now"
        if user.is_on_mobile():
            status = status + " Mobile"

        embed = discord.Embed(title="Account Info For: " + str(user) + " -- " + status,
                              description="Users Nickname: " + str(user.mention),timestamp=context.message.created_at)
        embed.add_field(name="Creation Date",value=str(user.created_at).split(".",1)[0])
        embed.add_field(name="Last Seen",value=str(lastonline))
        embed.add_field(name="Join Date",value=str(user.joined_at).split(".",1)[0],inline=True)


        print(user.activities)
        for activity in user.activities:
            print(str(activity))
            if str(activity) == "Spotify":
                link = "https://open.spotify.com/track/" + str(activity.track_id)
                embed.insert_field_at(index=5,name="Listening to",value="["+str(activity.title)+"]("+str(link)+")",inline=True)
            else:
                try:
                    emoji = activity.emoji
                    embed.insert_field_at(index=5,name="Status", value=str(activity.name), inline=True)
                except:
                    embed.insert_field_at(index=5,name="Playing", value=str(activity.name),inline=True)
        try:
            rapsheet = self.utility.getUserInfractions(guildID, user.id)
            embed.add_field(name="Infractions", value="Warnings: " + str(rapsheet["Warnings"])
                                                  + "; Mutes: " + str(rapsheet["Mutes"]) +
                                                  "; Kicks: " + str(rapsheet["Kicks"]),inline=False)
        except:
            pass

        roles = list(user.roles)
        roleString = str(roles[1].mention)
        for role in roles[2:]:
            roleString = str(role.mention) + ", " + roleString
        embed.add_field(name="Roles",value=roleString,inline=False)

        embed.set_thumbnail(url=user.avatar_url)

        embed.set_footer(text="UserID: " + str(user.id) + " • APPL: " + str(self.utility.getAPLevel(guild,user.id)) + " • Is Bot? " + str(user.bot))
        await context.send(embed=embed)