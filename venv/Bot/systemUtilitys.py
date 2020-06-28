import psutil, os
from Bot import AutoPilot
import distutils.dir_util as dirutils
A: float = 1

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
    red = AutoPilot.redSquare
    yellow = AutoPilot.yellowSquare
    green = AutoPilot.greenSquare

    level = 0
    light = green
    status = ""
    problems = []

    if load > 80:
        level += 1
        problems.append("High CPU Usage")
    if ram > 80:
        level += 1
        problems.append("High Memory Usage")
    if configSize > 125:
        level += 1
        problems.append("High Config Usage")
    if cache > maxCache/ 1.5:
        level += 1
        problems.append("High Cache Usage")
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

def updateClient(origin,target):
    print('Copy Started')
    if os.path.isdir(origin):
        print("Origin Exists, copying")
        dirutils.copy_tree(origin, target)
        print("Copy Finished")
        return True
    else:
        return False

