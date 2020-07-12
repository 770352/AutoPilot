from discord.ext import commands
import discord
import AutoPilot
import time


def setup(client):
    client.add_cog(ActivityModule(client))


class ActivityModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self._last_member = None

    def loadGuildStats(self, guildID):
        try:
            stats = AutoPilot.ServerSettings[str(guildID)]['ServerActivity']
        except KeyError:
            AutoPilot.ServerSettings[str(guildID)].update({"ServerActivity": {"NextReset": round(time.time() + 604800),
                                                                              "TotalMessages": 0, "RecentMessages": 0},
                                                           "ActivityTable": {}})
        stats = AutoPilot.ServerSettings[str(guildID)]['ServerActivity']
        return stats

    def loadUserStats(self, guildID, userID):
        try:
            stats = AutoPilot.ServerSettings[str(guildID)]['ActivityTable'][str(userID)]
        except KeyError as e:
            AutoPilot.ServerSettings[str(guildID)]['ActivityTable'].update({str(userID): {"PreviousStats": {
                "NextReset": round(time.time() + 604800), "avgActivity": 0, "totalMessages": 0, "totalSpam": 0},
                "RecentStats": {"messages": 0, "wordsSent": 0, "activity": 0, "lastMsgTime": round(time.time() - 15),
                                "recentSpam": 0}}})
        stats = AutoPilot.ServerSettings[str(guildID)]['ActivityTable'][str(userID)]
        return stats

    def loadActivityBreakdown(self, userID,guildID):
        try:
            pass
        except KeyError:
            breakdown = [0, 0, 0, 0]


    def saveStats(self, guildID, userID, serverStats, userStats):
        AutoPilot.ServerSettings[str(guildID)]['ServerActivity'] = serverStats
        AutoPilot.ServerSettings[str(guildID)]['ActivityTable'][str(userID)] = userStats

    def checkForReset(self, serverStats, userStats):
        resetTime = userStats['PreviousStats']["NextReset"]
        serverReset = serverStats['NextReset']
        if time.time() > resetTime:
            userStats['PreviousStats']["NextReset"] = round(time.time() + 604800)
            userStats['RecentStats']["wordsSent"] = 0
            userStats['RecentStats']["messages"] = 0
            userStats['RecentStats']['recentSpam'] = 0
            avgActivity = ((userStats['PreviousStats']["avgActivity"] * 3) + userStats["RecentStats"]["activity"]) / 4
            if avgActivity > 1:
                print("Invalid AvgActivity")
                avgActivity = 0

            print(str(userStats["RecentStats"]["activity"]) + ":" + str(avgActivity))
            userStats['PreviousStats']["avgActivity"] = avgActivity
            userStats['RecentStats']['activity'] = 0

        if time.time() > serverReset:
            print("Server Reset")
            serverStats['NextReset'] = round(time.time() + 604800)
            serverStats["RecentMessages"] = 0

        return serverStats, userStats

    def calculateValues(self, message, serverStat, userStat):
        serverStats, userStats = self.checkForReset(serverStat, userStat)
        totalwords = message.content
        totalwords = totalwords.split(" ")
        totalwords = len(totalwords)
        userStats['PreviousStats']['totalMessages'] += 1
        userStats['RecentStats']["messages"] += 1
        messages = userStats['RecentStats']["messages"]
        userStats['RecentStats']["wordsSent"] += totalwords
        userStats["RecentStats"]["lastMsgTime"] = round(time.time())
        serverStats["TotalMessages"] += 1
        serverStats["RecentMessages"] += 1
        totalMessages = serverStats["RecentMessages"]
        # quality = (userStats['RecentStats']["wordsSent"]/messages) * 0.25
        activity = ((messages) / totalMessages)
        if activity > 1:
            print("Invalid activity")
            return
        userStats["RecentStats"]["activity"] = activity
        self.saveStats(message.guild.id, message.author.id, serverStats, userStats)


    def updateStatusBreakdown(self, message):
        author = message.author
        status = author.status


    # Message Handler
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            serverStats = self.loadGuildStats(message.guild.id)
            userStats = self.loadUserStats(message.guild.id, message.author.id)
        except:
            return
        if message.author.bot:
            return
        if time.time() - userStats["RecentStats"]["lastMsgTime"] < 2.5:
            userStats["RecentStats"]["recentSpam"] += 1
            userStats["PreviousStats"]["totalSpam"] += 1
            return
        self.calculateValues(message, serverStats, userStats)
        self.updateStatusBreakdown(message)

    @commands.command()
    async def serverRank(self, context):
        guild = context.message.guild
        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ", 1)[1]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                user = context.message.author
        else:
            user = context.message.mentions[0]

        stats = self.loadGuildStats(guild.id)
        embed = discord.Embed(title="Activity Stats For: " + str(guild))
        embed.add_field(name="Total Messages", value=str(round(stats["TotalMessages"])))
        embed.add_field(name="Recent Messages", value=str(stats["RecentMessages"]))
        embed.set_footer(text="Next Reset Window: " + str(time.ctime(stats['NextReset'])))
        await context.send(embed=embed)

    @commands.command()
    async def rank(self, context):

        if not context.message.mentions:
            try:
                userID = str(context.message.content).split(" ", 1)[1]
                user = context.message.guild.get_member(int(userID))
                if not user:
                    await context.send("Invalid User ID")
                    return
            except IndexError:
                user = context.message.author
        else:
            user = context.message.mentions[0]

        stats = self.loadUserStats(context.message.guild.id, user.id)
        resetTime = stats["PreviousStats"]["NextReset"]
        embed = discord.Embed(title="Activity Stats For: " + str(user.nick))
        embed.add_field(name="Total Activity",
                        value=str(round(stats["PreviousStats"]["avgActivity"] * 10000) / 100) + "%")
        embed.add_field(name="Total Messages", value=str(stats["PreviousStats"]["totalMessages"]))
        embed.add_field(name="Total Spam", value=str(stats["PreviousStats"]["totalSpam"]))
        embed.add_field(name="Recent Activity", value=str(round(stats["RecentStats"]["activity"] * 10000) / 100) + "%")
        embed.add_field(name="Recent Messages", value=str(stats["RecentStats"]["messages"]))
        embed.add_field(name="Recent Spam", value=str(stats["RecentStats"]["recentSpam"]))
        embed.set_footer(text="Next Reset Window: " + str(time.ctime(resetTime)))
        await context.send(embed=embed)
        print("rank test")
