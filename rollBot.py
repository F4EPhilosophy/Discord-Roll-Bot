import discord
from discord.ext import commands
from discord.ext import tasks
import random
import time

from User import User
from Event import Event
from Server import Server

# Enable Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

server = Server()

@bot.event
async def on_ready():
    await bot.tree.sync()
    eventCheck.start()
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="rollwindowopen", description="Time to roll!")
async def rollwindowopen(interaction: discord.Interaction, item: str):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return

    if server.rollWindow == True:
        await interaction.response.send_message("Rolling is already in progress")
    else:   
        server.rollWindow = True
        server.rollWindowResults = []
        server.userRollCount = {}
        await interaction.response.send_message(f"@here You may begin rolling for: `{item}`")

@bot.tree.command(name="rollwindowclose", description="Stop all rolling.")
async def rollwindowclose(interaction: discord.Interaction):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    if server.rollWindow == False:
        await interaction.response.send_message("Rolling is already closed")
    elif not server.rollWindowResults:   
        await interaction.response.send_message("Roll window closed - No rolls logged")
    else:   
        server.rollWindow = False
        sortedResult = sorted(server.rollWindowResults, key=lambda x: x[1], reverse=True)
        await interaction.response.send_message("\n".join([f"`{name}: {number}`" for name, number in sortedResult]))

@bot.tree.command(name="roll", description="Rolls a number between 1 and 100")
async def roll(interaction: discord.Interaction):
    global server
    if not await server.validChannel(interaction):
        return

    number = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 You rolled a {number}! 🎲")

    if server.rollWindow == True:
        interName = interaction.user.name
        interNick = interaction.user.nick if interaction.user.nick != None else interName
        interID = interaction.user.id

        user = server.findUser(interID)
        if user != None:
            user.updateUser(user.id, interNick, interName, user.extraRolls, user.dkp)

        if interID not in server.userRollCount:
            server.userRollCount[interID] = 1
            server.rollWindowResults.append((interNick, number))
        elif user == None or user.extraRolls == 0:
            await interaction.followup.send(f"{interaction.user.mention} you have no extra rolls avalible")
            await interaction.delete_original_response()
        elif server.userRollCount[user.id] < 2 and user.extraRolls > 0:
            server.userRollCount[user.id] += 1
            user.extraRolls -= 1
            server.rollWindowResults.append((interNick, number))
        else:   
            await interaction.followup.send(f"{interaction.user.mention} you have already rolled twice, your {number} will be ignored.")
            await interaction.delete_original_response()

    server.saveUserFile()

@bot.tree.command(name="addroll", description="Gives a user an extra roll to use later")
async def addroll(interaction: discord.Interaction, member: discord.Member):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    user = server.findUser(member.id)
    if user == None:
        user = User(member.id, member.nick, member.name, 0)
        server.users.append(user)
    
    user.extraRolls += 1
    server.saveUserFile()
    await interaction.response.send_message(f"{user.nickName} has been given an extra roll.")

@bot.tree.command(name="removeroll", description="Removes an extra roll from a user if they have one")
async def removeroll(interaction: discord.Interaction, member: discord.Member):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    user = server.findUser(member.id)   

    if user == None or user.extraRolls == 0:
        await interaction.response.send_message(f"{member.name} has no extra rolls.")
    else:
        await interaction.response.send_message(f"{member.name} has had an extra roll taken away.")
        user.extraRolls -= 1
    server.saveUserFile()

@bot.tree.command(name="adddkp", description="Gives a user an extra roll to use later")
async def adddkp(interaction: discord.Interaction, member: discord.Member, amount: int):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    user = server.findUser(member.id)
    if user == None:
        user = User(member.id, member.nick, member.name, 0, amount)
        server.users.append(user)
    else:
        user.dkp += amount
    await interaction.response.send_message(f"{member.name} has had {amount} DKP added.")
    server.saveUserFile()

@bot.tree.command(name="removedkp", description="Gives a user an extra roll to use later")
async def removedkp(interaction: discord.Interaction, member: discord.Member, amount: int):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    user = server.findUser(member.id)
    if user == None:
        user = User(member.id, member.nick, member.name, 0, amount)
        server.users.append(user)
    else:
        user.dkp -= amount
    await interaction.response.send_message(f"{member.name} has had {amount} DKP removed.")
    server.saveUserFile()

@bot.tree.command(name="extrarolls", description="How many extra rolls you have.")
async def extrarolls(interaction: discord.Interaction):
    global server
    if not await server.validChannel(interaction):
        return
    
    user = server.findUser(interaction.user.id)
    await interaction.response.send_message(f"You have {0 if user == None else user.extraRolls} extra roll(s)")

@bot.tree.command(name="extrarollsearch", description="How many extra rolls someone else has.")
async def extrarollsearch(interaction: discord.Interaction, member: discord.Member):
    global server
    if not await server.validChannel(interaction) and not await server.validRole(interaction):
        return
    
    user = server.findUser(member.id)
    await interaction.response.send_message(f"{member.name} has {0 if user == None else user.extraRolls} extra roll(s)")

@bot.tree.command(name="extrarolltable", description="Table of users extra rolls. Users with none may not appear.")
async def extrarolltable(interaction: discord.Interaction, rows: int):
    global server
    if not await server.validChannel(interaction) and not await server.validRole(interaction):
        return
    sortedUsers = sorted(server.users, key=lambda x: x.extraRolls, reverse=True)
    if len(sortedUsers) == 0:
        response = "Nobody has any extra rolls."
    else:
        response = "\n".join([f"`Name: {user.nickName}, Extra rolls: {user.extraRolls}`" for user in sortedUsers[0:rows]])
    await interaction.response.send_message(f"{response}")

@bot.tree.command(name="setchannel", description="Designates a channel to use all commands in.")
async def setchannel(interaction: discord.Interaction):
    global server
    if not await server.validRole(interaction):
        return

    server.rollChannelID = interaction.channel.id
    server.saveConfig()

    await interaction.response.send_message("Channel Set")
    
@bot.tree.command(name="setrole", description="Set the role allowed to use open/close window + add/remove extra rolls.")
@commands.has_permissions(administrator=True)
async def setrole(interaction: discord.Interaction, id: str):
    global server
    server.roleID = int(id)
    server.saveConfig()
    
    await interaction.response.send_message("Role Set")

@bot.tree.command(name="createlisting", description="Creates a thread for item listing.")
async def createlisting(interaction: discord.Interaction, item: str, trait: str):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    starter_message = await interaction.channel.send(f"Listing for **{item}** with **{trait}** has been created.")
    await starter_message.create_thread(name = f"{item} - {trait}", auto_archive_duration = 1440)

@bot.tree.command(name="mydkp", description="Check how much DKP you have.")
async def mydkp(interaction: discord.Interaction):
    global server
    if not await server.validChannel(interaction):
        return
   
    user = server.findUser(interaction.user.id)
    channel = await interaction.user.create_dm()

    await channel.send(f"You have {user.dkp} DKP")

@bot.tree.command(name="dkpsearch", description="search specific users dkp.")
async def dkpsearch(interaction: discord.Interaction, member: discord.Member):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    channel = await interaction.user.create_dm()
    user = server.findUser(member.id)
    
    await channel.send(f"{member.name} has {0 if user == None else user.dkp} dkp")

@bot.tree.command(name="dkptable", description="Print table of DKP")
async def tabledkp(interaction: discord.Interaction, rows: int):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return
    
    channel = await interaction.user.create_dm()
    sortedUsers = sorted(server.users, key=lambda x: x.dkp, reverse=True)

    if len(sortedUsers) == 0:
        response = "No users in dkp list. Maybe no one has dkp?"
    else:
        response = "\n".join([f"`Name: {user.nickName}, DKP: {user.dkp}`" for user in sortedUsers[0:rows]])
    await channel.send(f"{response}")

@bot.tree.command(name="addevent", description="Gives a user an extra roll to use later")
async def addevent(interaction: discord.Interaction, time: str, duration: int, name: str, dkp: int, recurring: bool):
    global server
    if not await server.validChannel(interaction) or not await server.validRole(interaction):
        return

    for event in server.events:
        if event.time == time:
            await interaction.response.send_message(f"There is already an event at that start time!")

    newEvent = Event(time, duration, name, dkp, recurring)
    if len(server.events) == 0:
        server.events.append(newEvent)
    else:
        for idx, event in enumerate(server.events):
            if newEvent.time < event.time:
                server.events.insert(idx, newEvent)
    await interaction.response.send_message(f"Event added!")
    server.saveEventSchedule()

@tasks.loop(seconds=30)
async def eventCheck():
    global server
    guild = bot.get_guild(server.serverID)

    currTime = time.strptime(time.ctime(time.time()))
    currHour = currTime.tm_hour
    currMinute = currTime.tm_min

    if server.eventOpen:
        event = server.currEvent
        eventHour = int(event.time[0:2])
        eventMinute = int(event.time[3:5])
        if server.eventStarted:
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 60, event.duration):
                server.eventEndAttendance = server.eventVoiceChannel.members.copy()
                fullAttendance = []
                partialAttendance = []
                for memberEnd in server.eventEndAttendance:
                    for memberStart in server.eventStartAttendance:
                        if memberStart.id == memberEnd.id:
                            fullAttendance.append(memberStart)
                
                for member in fullAttendance:
                    user = server.findUser(member.id)
                    if user == None:
                        user = User(member.id, member.nick, member.name, 0, event.dkp)
                        server.users.append(user)
                    else:
                        user.dkp += event.dkp
                    break
                server.saveUserFile()

                #Display message of members who attended and got dkp, and list of member who showed up late or left early

                await server.eventVoiceChannel.delete()
                server.eventVoiceChannel = None
                server.eventStartAttendance = []
                server.eventEndAttendance = []
                server.eventVoiceChannel = None
                server.eventStarted = False
                server.eventOpen = False
        else:
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 5, 0):
                server.eventStarted = True
                server.eventStartAttendance = server.eventVoiceChannel.members.copy()
    else:
        for event in server.events:
            eventHour = int(event.time[0:2])
            eventMinute = int(event.time[3:5])
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 0, -5):
                server.eventOpen = True
                server.currEvent = event
                server.eventVoiceChannel = await guild.create_voice_channel(name=server.currEvent.name)

def withinTimeRange(currHour, currMinute, checkHour, checkMinute, topRange, bottomRange):
    topRange = wrapTime(checkHour, checkMinute + topRange)
    bottomRange = wrapTime(checkHour, checkMinute + bottomRange)
    if bottomRange[0] < currHour or bottomRange[0] == currHour and bottomRange[1] <= currMinute:
        if topRange[0] > currHour or topRange[0] == currHour and topRange[1] >= currMinute:
            return True
    return False

def wrapTime(hour, minute):
    if minute >= 60:
        minute -= 60
        hour += 1
    elif minute < 0:
        minute += 60
        hour -= 1
    return hour, minute
        
with open("API-Key.txt", "r", encoding='utf-8-sig') as f:
    apiKey = f.read()
    f.close()

bot.run(apiKey)