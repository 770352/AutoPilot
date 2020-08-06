import psutil, os
from discord.ext import commands
import discord
import distutils.dir_util as dirutils
currentMode = None
clientName = None
trusted = []
ServerSettings = {}
greenSquare = "https://media.discordapp.net/attachments/515326457652707338/723982716219162725/450.png"
yellowSquare = "https://media.discordapp.net/attachments/515326457652707338/723986430421893160/adidas-adi" \
               "color-yellow-orange-square-shape-s-png-clip-art.png?width=668&height=587"
redSquare = "https://media.discordapp.net/attachments/515326457652707338/723982767326625832/CCS400RD.png?" \
            "width=587&height=587"
atcInvite = "https://discord.gg/qcFBMSS"

class NotAuthorized(Exception):
    pass

def isAdmin(guildID, userID):
    try:
        return int(userID) in ServerSettings[str(guildID)]["ServerStaff"]["Admins"]
    except KeyError:
        return False

def isMod(guildID, userID):
    try:
        return int(userID) in ServerSettings[str(guildID)]["ServerStaff"]["Mods"]
    except KeyError:
        return False

def getAPLevel(guild, userID):
    if str(userID) in trusted:
        return 4
    elif userID == guild.owner_id:
        return 3
    elif isAdmin(guild.id, userID):
        return 2
    elif isMod(guild.id, userID):
        return 1
    else:
        return 0

def userIsAuthorized(required):
    """Decorator to check if bot has certain permissions when added to a command"""
    def predicate(context):
        """Function to tell if the user has the right permissions"""
        missing = False

        guild = context.message.guild
        if not getAPLevel(guild, context.message.author.id) >= required:
            missing = True

        if missing:
            return False
        else:
            return True

    def decorator(func):
        """Defines the bot_has_permissions decorator"""
        if isinstance(func, commands.Command):
            func.checks.append(predicate)
        else:
            if hasattr(func, '__commands_checks__'):
                func.__commands_checks__.append(predicate)
            else:
                func.__commands_checks__ = [predicate]
        return func
    return decorator


def memory():
    Result = psutil.virtual_memory()
    gb = 1073741824
    totalram = Result[0]
    totalram = str(totalram / gb)
    usedram = Result[3]
    usedram = str(usedram / gb)
    percent = Result[2]
    ram = str(usedram[:4]) + "GB/" + str(totalram[:4]) + "GB, " + str(percent) + "%"
    return ram, percent

def configSize(configPath):
    byteSize = os.path.getsize(configPath)
    kb = 1000
    return byteSize/kb

def uptimeStamp(c):

    days = c // 86400
    hours = c // 3600 % 24
    minutes = c // 60 % 60
    seconds = c % 60

    return ("{days} Days, {hours} Hours, {minutes} Minutes, and {seconds} Seconds").format(
                                                                    days = round(days),
                                                                    hours = round(hours),
                                                                    minutes= round(minutes),
                                                                    seconds = round(seconds))

def getStatus(load, ram, configSize, heartbeat, ping, cache, maxCache):
    red = redSquare
    yellow = yellowSquare
    green = greenSquare

    level = 0
    light = green
    status = ""
    problems = []

    if currentMode == "Rebooting":
        level += 2
        problems.append("AutoPilot Is Rebooting...")
    if currentMode == "ShuttingDown":
        level += 2
        problems.append("AutoPilot Has ShutDown")
    if currentMode == "Updating":
        level += 1
        problems.append("AutoPilot Is Updating...")
    if currentMode == "Restarting":
        level += 1
        problems.append("AutoPilot Is Restarting...")

    if load > 80:
        level += 1
        problems.append("High CPU Usage")
    if ram > 80:
        level += 1
        problems.append("High Memory Usage")
    if configSize > 1250:
        #level += 1
        #problems.append("High Config Usage")
        pass
    if heartbeat > 1000:
        level += 1
        problems.append("High API Latency")
    if ping > 1000:
        level += 1
        problems.append("High Command Latency")
    if level >= 2:
        light = red
        status = "Multiple System Faults"
    elif level >= 1:
        light = yellow
        status = "Single System Fault"
    else:
        light = green
        status = "All Systems Operational"
    if len(problems) == 0:
        return status, light, None
    elif len(problems) == 1:
        return status, light, problems[0]
    else:
        probString = problems[0]
        for problem in problems[1:]:
            probString = probString + ", " + problem
        return status, light, probString

def updateClient():
    cmdResult = os.popen('git pull').read()
    print("Result: " + str(cmdResult))
    if cmdResult.startswith('Already up to date.'):
        return 0
    elif cmdResult.startswith("Updating"):
        return 1
    else:
        return -1


