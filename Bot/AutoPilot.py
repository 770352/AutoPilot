from discord.ext import commands
import os
import discord
import asyncio
import time, json

from Bot import AutoPilot, systemUtilitys
import sys, inspect, types, psutil
import _thread as threads
version = "0.4.0"
trusted = ['435450974778294273']
cogs = {}
ServerSettings = {}
Running = True
config = open("C:\AutoPilot_Files-V3\Config.txt", "r")
listoflines4 = config.readlines()
config = [s.replace("\n", "") for s in listoflines4]
TOKEN = config[0]
DEFAULT_PREFIX = config[1]
Profiles = config[2]
greenSquare = "https://media.discordapp.net/attachments/515326457652707338/723982716219162725/450.png"
yellowSquare = "https://media.discordapp.net/attachments/515326457652707338/723986430421893160/adidas-adi" \
               "color-yellow-orange-square-shape-s-png-clip-art.png?width=668&height=587"
redSquare = "https://media.discordapp.net/attachments/515326457652707338/723982767326625832/CCS400RD.png?" \
            "width=587&height=587"
atcInvite = "https://discord.gg/qcFBMSS"



if os.path.isfile(Profiles):
    try:
        with open(Profiles, "r") as f:
            ServerSettings = json.load(f)
    except:
        print("Failed Load")


def dynamicPrefix(client,message):
    try:
        prefix = AutoPilot.ServerSettings[str(message.guild.id)]["ServerSettings"]["prefix"]
    except:
        prefix = DEFAULT_PREFIX
    return prefix


def save():
    if os.path.isfile(Profiles):
        with open(Profiles, "w") as f:
            ServerSettings["ProfilesInfo"]["LastSaveRaw"] = round(time.time())
            ServerSettings["ProfilesInfo"]["LastSave"] = time.ctime()
            json.dump(ServerSettings, fp=f, sort_keys=True, indent=4)


def autoSave(garbo1, garbo2, ForceSave=False):
    global Running, ServerSettings
    print("AutoSave Has Started")
    while not ForceSave and Running:
        save()
        time.sleep(300)


class ManagmentModule(commands.Cog):
    def __init__(self, bot):
        self.client = bot


    async def accessWebsite(self,context):
        embed = discord.Embed(title="Example Stuff: " + str(user) + " -- " + status,
                              description="Extra example: " + str(user.mention), timestamp=context.message.created_at)
        link = "https://discord.com/api/oauth2/authorize?client_id=514999044444127233&redirect_uri=https%3A%2F%2F71.227.29.98%3A47675&response_type=code&scope=identify%20email"
        embed.add_field(name="Website",value="[website]("+str(link)+")")

    async def Ping(self,context):
        time0 = time.time()
        channel = context.channel
        async with channel.typing():
            time1 = time.time()
            ping = ((time1 - time0) * 1000) / 2
        heartbeat = round(client.latency * 1000)
        return (ping,heartbeat)

    async def traffic(self,mode):
        old_value = 0
        send_stat = 0
        count = 0
        while (count < 2):
            new_value = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            if old_value:
                send_stat = new_value - old_value
            old_value = new_value
            print(str(send_stat))
            if send_stat > 1000000:
                network = (send_stat / 1000000) * 8
                val = "Mbps"
            else:
                network = (send_stat / 1000) * 8
                val = "Kbps"
            count = count + 1
            await asyncio.sleep(1)
        network = str(network)
        networkA = network.split(".", 2)
        networkB = networkA[1]
        networkB = networkB[:2]
        network = networkA[0] + "." + networkB + " " + str(val)
        if mode is 0:
            return send_stat
        if mode is 1:
            return network

    @commands.command()
    async def ping(self, context):
        time0 = time.time()
        channel = context.channel
        async with channel.typing():
            time1 = time.time()
            ping = ((time1 - time0) * 1000) / 2
        heartbeat = round(client.latency * 1000)
        await context.send("Ping: " + str(round(ping)) + "ms\nHeartbeat: " + str(heartbeat) + "ms")

    @commands.command()
    async def setprefix(self,context,prefix):
        user = context.message.author
        guild = context.message.guild
        if self.modCog.getAPLevel(guild,user.id):
            AutoPilot.ServerSettings[str(context.message.guild.id)]["ServerSettings"].update({"prefix": str(prefix)})
            await context.send("Prefix Set To: " + str(prefix))

    @commands.command()
    @commands.is_owner()
    async def save(self, context):
        save()
        await context.send("Saved")

    @commands.command()
    @commands.is_owner()
    async def update(self,context):
        save()
        await context.send("Initating File Transfer")
        status = systemUtilitys.updateClient("\\\\MAINPC\\Users\\aidan\PycharmProjects\Dumpsterfire_V3\\venv",
                                    "C:\\Users\\AutoPilot\\PycharmProjects\AutoPilot_V3\\venv")
        if status:
            await context.send("Restarting...")
            exit(0)
        else:
            await context.send("Update Failed")


    @commands.command(aliases=['restart'])
    @commands.is_owner()
    async def closeDown(self,context):
        save()
        await context.send("AutoPilot Logging Off")
        await client.logout()
        exit(0)

    @commands.command()
    @commands.is_owner()
    async def terminate(self,context):
        await context.send("Hard Stopping The AutoPilot Executable")
        exit(-1)
        await context.send("Failed To Stop")

    @commands.command()
    @commands.is_owner()
    async def reloadCog(self, context, cog):
        cogs[str(cog)] = {"Restarting": "Being Removed"}
        self.client.remove_cog(cog)
        cogs[str(cog)] = {"Restarting": "Removed"}


    @commands.command()
    async def invite(self,context):
        await context.send("https://discord.com/api/oauth2/authorize?client_id=514999044444127233&permissions=8&redirect"
                           "_uri=https%3A%2F%2Fdiscord.com&scope=bot")

    @commands.command()
    async def diagnostics(self,context):
        ping, heartbeat = await self.Ping(context)
        #traffic = self.traffic(0)
        load = psutil.cpu_percent()
        ram, Rpercent = systemUtilitys.memory()
        configSize = round(systemUtilitys.configSize(Profiles) * 10) / 10

        cache = len(self.client.cached_messages)
        maxCache = 2500
        serverUptime = systemUtilitys.uptimeStamp(time.time() - psutil.boot_time())
        clientUptime = systemUtilitys.uptimeStamp(time.clock())

        clientName = (context.message.guild.get_member(int(self.client.user.id))).nick
        status, statusLight, error = systemUtilitys.getStatus(load, Rpercent, configSize, heartbeat, ping, cache, maxCache)

        embed = discord.Embed(title=status,
                              timestamp=context.message.created_at)
        if error:
            embed.description = error
        embed.set_author(name=str(clientName) + " Diagnostics",icon_url=statusLight,url=atcInvite)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(name="CPU Usage",value=str(load)+"%",inline=True)
        embed.add_field(name="Memory Usage",value=str(ram))
        embed.add_field(name="Config Size",value=str(configSize) + "KB")
        embed.add_field(name="Cog Stats",value=str(len(cogs)-1)+"/"+str(len(cogs)))
        embed.add_field(name="Cache usage",value=str(cache) + "/" + str(maxCache) + " Messages")
        embed.add_field(name="API Latency",value=str(heartbeat) + "ms")
        embed.add_field(name="Server Uptime",value=str(serverUptime),inline=False)
        embed.add_field(name="Client Uptime",value=str(clientUptime),inline=False)
        embed.set_footer(text="Version: " + str(version))
        await context.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def prugeCache(self,context):
        await context.send("Purging client cache, please wait")
        client.clear()
        await context.send("Client cache pruged")

    @commands.command()
    async def cogs(self,context):
        embed = discord.Embed(title="Cog Ops")
        for cog,stat in cogs.items():
            for status,code in stat.items():
                    embed.add_field(name=cog ,value=status + ": " + code)
        await context.send(embed=embed)


def is_client(message):
    return message.author == client.user


async def live_stats(channelID):
    oldMessage = None
    embed = None
    channel = client.get_channel(channelID)
    await channel.purge(limit=100,check=is_client)
    while True:
        #ping, heartbeat = await self.Ping(context)
        ping = 0
        try:
            heartbeat = round(client.latency * 1000)
        except OverflowError:
            heartbeat = 9999999999
        # traffic = self.traffic(0)
        load = psutil.cpu_percent()
        ram, Rpercent = systemUtilitys.memory()
        configSize = round(systemUtilitys.configSize(Profiles) * 10) / 10

        cache = len(client.cached_messages)
        maxCache = 2500
        serverUptime = systemUtilitys.uptimeStamp(time.time() - psutil.boot_time())
        clientUptime = systemUtilitys.uptimeStamp(time.clock())

        clientName = (channel.guild.get_member(int(client.user.id))).nick
        status, statusLight, error = systemUtilitys.getStatus(load, Rpercent, configSize, heartbeat, ping, cache, maxCache)
        if embed:
            embed = discord.Embed(title=status)
        else:
            embed = discord.Embed(title=status)
        if error:
            embed.description = error
        embed.set_author(name=str(clientName) + " Diagnostics", icon_url=statusLight, url=atcInvite)
        #embed.set_thumbnail(url=client.user.avatar_url)
        embed.add_field(name="CPU Usage", value=str(load) + "%", inline=True)
        embed.add_field(name="Memory Usage", value=str(ram))
        embed.add_field(name="Config Size", value=str(configSize) + "KB")
        embed.add_field(name="Cog Stats", value=str(len(cogs) - 1) + "/" + str(len(cogs)))
        embed.add_field(name="Cache usage", value=str(cache) + "/" + str(maxCache) + " Messages")
        embed.add_field(name="API Latency", value=str(heartbeat) + "ms")
        embed.add_field(name="Server Uptime", value=str(serverUptime), inline=False)
        embed.add_field(name="Client Uptime", value=str(clientUptime), inline=False)
        embed.set_footer(text="Version: " + str(version) + " • " + str(time.ctime()))
        if oldMessage:
            await oldMessage.edit(embed=embed)
        else:
            oldMessage = await channel.send(embed=embed)
        await asyncio.sleep(5)


DEFAULT_PREFIX = "-"
displayed = discord.CustomActivity(name="Being Developed")
client = commands.Bot(dynamicPrefix,case_insensitive=True,activity=displayed,max_messages=2500)
client.add_cog(ManagmentModule(client))
cogs["ManagementModule"] = {"Running":"No Problems"}
cogs["SystemUtilitys"] = {"Running":"No Problems"}
time.sleep(1)
for ext in os.listdir('C:\\Users\\aidan\\PycharmProjects\\Dumpsterfire_V3\\Bot\\Cogs'):
    if not ext.startswith(('_', '.')):
        client.load_extension('Cogs.' + ext[:-3])


@client.event
async def on_ready():
    print(str(client.user) + " Has Started And Is Connected To Discord")
    guilds = await client.fetch_guilds(limit=150).flatten()
    for guild in guilds:
        try:
            id = ServerSettings[str(guild.id)]
        except KeyError as e:
            ServerSettings.update({str(guild.id):{"ServerSettings":{}}})
    threads.start_new(autoSave,(0,0))
    displayed = discord.CustomActivity(name="Being Developed")
    await client.change_presence(status=discord.Status.online,activity=displayed)
    await client.loop.create_task(live_stats(726106253809418261))

while Running:
    try:
        client.loop.run_until_complete(client.start(TOKEN))
    except Exception as e:
        print(str(e))
