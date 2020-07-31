from discord.ext import commands
import os
import discord
import asyncio
import time, json, traceback, sys

import systemUtilitys
import psutil
import _thread as threads

startTime = time.time()

version = "0.4.8"
trusted = ['435450974778294273']
banned = []
cogs = {}
ServerSettings = {}
Running = True
config = open("C:\\AutoPilot_Files-V3\\Config.txt", "r")
listoflines4 = config.readlines()
config = [s.replace("\n", "") for s in listoflines4]
TOKEN = config[0]
DEFAULT_PREFIX = config[1]
Profiles = config[2]
CogLocations = config[3]
greenSquare = "https://media.discordapp.net/attachments/515326457652707338/723982716219162725/450.png"
yellowSquare = "https://media.discordapp.net/attachments/515326457652707338/723986430421893160/adidas-adi" \
               "color-yellow-orange-square-shape-s-png-clip-art.png?width=668&height=587"
redSquare = "https://media.discordapp.net/attachments/515326457652707338/723982767326625832/CCS400RD.png?" \
            "width=587&height=587"
atcInvite = "https://discord.gg/qcFBMSS"
stacktracebuffer = None

if os.path.isfile(Profiles):
    try:
        with open(Profiles, "r") as f:
            ServerSettings = json.load(f)
    except:
        print("Failed Load")


def dynamicPrefix(client, message):
    try:
        prefix = ServerSettings[str(message.guild.id)]["ServerSettings"]["prefix"]
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

    async def Ping(self, context):
        time0 = time.time()
        channel = context.channel
        messageTime = context.message.created_at
        print(str(messageTime.timestamp()) + ":" + str(time.time()))
        messageDelay = round(int(time.time()) - int(messageTime.timestamp()) / 1000)
        async with channel.typing():
            time1 = time.time()
            ping = ((time1 - time0) * 1000) / 2
        heartbeat = round(client.latency * 1000)
        return ping, heartbeat, messageDelay

    async def traffic(self, mode):
        old_value = 0
        send_stat = 0
        count = 0
        while count < 2:
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


    @commands.command(brief="Returns the client to discord latency")
    async def ping(self, context):
        ping, heartbeat, messageDelay = await self.Ping(context)
        await context.send("Ping: " + str(round(ping)) + "ms\nHeartbeat: " + str(heartbeat) + "ms")

    @commands.command(brief="Force saves the config file; Host only")
    @commands.is_owner()
    async def save(self, context):
        save()
        await context.send("Saved")

    @commands.is_owner()
    @commands.command(name='update', brief="Updates client and then restarts the client; Host Only")
    async def update(self, context):
        save()
        message = await context.send("Preparing To Update Client")
        res = systemUtilitys.updateClient()
        if res == 0:
            await message.edit(content="Client Already Up To Date")
        elif res == 1:
            await message.edit(content="Client Updated, Restarting")
            await client.logout()
            exit(2)
        else:
            await message.edit(content="Something Went Wrong, Aborting")

    @commands.command(aliases=['restart'], brief='Disconnects AutoPilot; Host only')
    @commands.is_owner()
    async def closeDown(self, context):
        save()
        await context.send("AutoPilot Logging Off")
        await client.logout()
        exit(0)

    @commands.command(brief="Hard stops the client; Host only")
    @commands.is_owner()
    async def terminate(self, context):
        await context.send("Hard Stopping The AutoPilot Executable")
        exit(-1)
        await context.send("Failed To Stop")

    @commands.command(brief="Reboots AutoPilots Host Machine; Host Only")
    @commands.is_owner()
    async def reboot(self, context):
        await context.send("Rebooting")
        save()
        await client.logout()
        os.system('shutdown /r /f')
        exit(0)

    @commands.command(brief="Returns an the bot invite link")
    async def invite(self, context):
        await context.send(
            "https://discord.com/api/oauth2/authorize?client_id=514999044444127233&permissions=8&redirect"
            "_uri=https%3A%2F%2Fdiscord.com&scope=bot")

    @commands.command(brief='List Client Status, and statistics')
    async def diagnostics(self, context):
        ping, heartbeat, messageDelay = await self.Ping(context)
        # traffic = self.traffic(0)
        load = psutil.cpu_percent()
        ram, Rpercent = systemUtilitys.memory()
        configSize = round(systemUtilitys.configSize(Profiles) * 10) / 10

        cache = len(self.client.cached_messages)
        maxCache = 2500
        serverUptime = systemUtilitys.uptimeStamp(time.time() - psutil.boot_time())
        clientUptime = systemUtilitys.uptimeStamp(time.time() - startTime)

        clientName = (context.message.guild.get_member(int(self.client.user.id))).nick
        status, statusLight, error = systemUtilitys.getStatus(load, Rpercent, configSize, heartbeat, ping, cache,
                                                              maxCache)

        embed = discord.Embed(title=status,
                              timestamp=context.message.created_at)
        if error:
            embed.description = error
        embed.set_author(name=str(clientName) + " Diagnostics", icon_url=statusLight, url=atcInvite)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.add_field(name="CPU Usage", value=str(load) + "%", inline=True)
        embed.add_field(name="Memory Usage", value=str(ram))
        embed.add_field(name="Config Size", value=str(configSize) + "KB")
        embed.add_field(name="Cog Stats", value=str(len(cogs) - 1) + "/" + str(len(cogs)))
        embed.add_field(name="Cache usage", value=str(cache) + "/" + str(maxCache) + " Messages")
        embed.add_field(name="API Latency", value=str(heartbeat) + "ms")
        embed.add_field(name="Server Uptime", value=str(serverUptime), inline=False)
        embed.add_field(name="Client Uptime", value=str(clientUptime), inline=False)
        embed.set_footer(text="Version: " + str(version))
        await context.send(embed=embed)

    @commands.command(brief="Clears the message cache and reloads the bot; Host only")
    @commands.is_owner()
    async def prugeCache(self, context):
        await context.send("Purging client cache, please wait")
        client.clear()
        await context.send("Client cache purged")

    @commands.command(brief="Returns the most recent error's traceback, Host Only")
    @commands.is_owner()
    async def traceback(self, context):
        if len(stacktracebuffer[1]) > 2000:
            await context.send(
                "This error was too catastrophic to be able to print to discord, error was saved to logs")
            return
        await context.send("```" + str(stacktracebuffer[1]) + "```")

    async def errorCreator(self, context):
        await self.createError(context)

    @commands.command(brief="testing error handler")
    @commands.is_owner()
    async def createError(self, context):
        raise NotImplementedError
        await self.errorCreator(context)


def is_client(message):
    return message.author == client.user


async def live_stats(channelID):
    oldMessage = None
    embed = None
    try:
        channel = client.get_channel(channelID)
        await channel.purge(limit=100, check=is_client)
        while True:
            # ping, heartbeat = await self.Ping(context)
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
            clientUptime = systemUtilitys.uptimeStamp(time.time() - startTime)

            clientName = (channel.guild.get_member(int(client.user.id))).nick
            status, statusLight, error = systemUtilitys.getStatus(load, Rpercent, configSize, heartbeat, ping, cache,
                                                                  maxCache)
            if embed:
                embed = discord.Embed(title=status)
            else:
                embed = discord.Embed(title=status)
            if error:
                embed.description = error
            embed.set_author(name=str(clientName) + " Diagnostics", icon_url=statusLight, url=atcInvite)
            # embed.set_thumbnail(url=client.user.avatar_url)
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
    except Exception as e:
        print(str(e))
        await client.loop.create_task(live_stats(726106253809418261))


DEFAULT_PREFIX = "-"
displayed = discord.CustomActivity(name="Being Developed")
client = commands.Bot(dynamicPrefix, case_insensitive=True, activity=displayed, max_messages=2500)
client.add_cog(ManagmentModule(client))
cogs["ManagementModule"] = {"Running": "No Problems"}
cogs["SystemUtilitys"] = {"Running": "No Problems"}
time.sleep(1)
client.remove_command('help')
for ext in os.listdir(CogLocations):
    if not ext.startswith(('_', '.', '-')):
        print("Loading Extenstion: " + str(ext[:-3]))
        try:
            client.load_extension('Cogs.' + ext[:-3])
        except Exception as e:
            print("Failed to load Extension: " + str(ext[:-3] + "; Reason: " + str(e)))



@client.event
async def on_ready():
    print(str(client.user) + " Has Started And Is Connected To Discord")
    guilds = await client.fetch_guilds(limit=150).flatten()
    for guild in guilds:
        try:
            id = ServerSettings[str(guild.id)]
        except KeyError:
            ServerSettings.update({str(guild.id): {"ServerSettings": {}}})
    threads.start_new(autoSave, (0, 0))
    displayed = discord.CustomActivity(name="Being Developed")
    await client.change_presence(status=discord.Status.online, activity=displayed)
    await client.loop.create_task(live_stats(726106253809418261))


@client.event
async def on_message(message):
    if str(message.author.id) in banned:
        return
    await client.process_commands(message)
    pass

@client.event
async def on_command_error(context, exception):
    global stacktracebuffer
    guild = context.message.guild
    if isinstance(exception, commands.CommandNotFound):
        return
    stacktracebuffer = \
        [exception, ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))]
    errorType = str(exception)
    print(str(stacktracebuffer[1]))

    embed = discord.Embed(title=client.user.name + " has encountered an error", color=0xFF0000,
                          description="Error: \"" + str(errorType) + "\"")
    embed.add_field(name="Invoked Command", value=str(context.message.content))
    await context.send(embed=embed)


while Running:
    try:
        client.loop.run_until_complete(client.start(TOKEN))
        time.sleep(10)
    except Exception as e:
        print("Close Out Error: " + str(e))
