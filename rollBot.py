import discord
from discord.ext import commands
from discord.ext import tasks
import random
import time

from helper import *
from DKP import DKP
from Rolling import Rolling
from User import User
from Event import Event
from Server import Server

# Enable Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
bot.server = Server()

@bot.event
async def on_ready():
    await bot.add_cog(DKP(bot))
    await bot.add_cog(Rolling(bot))
    await bot.tree.sync()
    eventCheck.start()
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="setmaxrolls", description="Set max # of rolls per open window")
async def setmaxrolls(interaction: discord.Interaction, max_roll_count: int):
    if not await bot.server.validChannel(interaction) or not await bot.server.validRole(interaction):
        return
        
    if max_roll_count < 1:
        await interaction.response.send_message("You can not set a number lower than 1")
        return
    if max_roll_count == bot.server.maxRolls:
        await interaction.response.send_message(f"The current # of rolls is already set to {max_roll_count}")
        return
    else:
        bot.server.maxRolls = max_roll_count
        await interaction.response.send_message(f"Max # of rolls = {max_roll_count}")
    bot.server.saveConfig()

@bot.tree.command(name="setrole", description="Set the role allowed to use admin commands.")
@commands.has_permissions(administrator=True)
async def setrole(interaction: discord.Interaction, id: str):
    bot.server.roleID = int(id)
    bot.server.saveConfig()
    
    await interaction.response.send_message("Role Set")

@bot.tree.command(name="setchannel", description="Designates a channel to use all commands in.")
async def setchannel(interaction: discord.Interaction):
    if not await bot.server.validRole(interaction):
        return

    bot.server.rollChannelID = interaction.channel.id
    bot.server.saveConfig()
    await interaction.response.send_message("Channel Set")

@bot.tree.command(name="addevent", description="creates dkp event")
async def addevent(interaction: discord.Interaction, time: str, duration: int, name: str, dkp: int, recurring: bool):
    if not await bot.server.validChannel(interaction) or not await bot.server.validRole(interaction):
        return

    for event in bot.server.events:
        if event.time == time:
            await interaction.response.send_message(f"There is already an event at that start time!")

    newEvent = Event(time, duration, name, dkp, recurring)
    if len(bot.server.events) == 0:
        bot.server.events.append(newEvent)
    else:
        for idx, event in enumerate(bot.server.events):
            if newEvent.time < event.time:
                bot.server.events.insert(idx, newEvent)
                break
            elif idx == len(bot.server.events)-1:
                bot.server.events.append(newEvent)
                break
    await interaction.response.send_message(f"Event added!")
    bot.server.saveEventSchedule()

@tasks.loop(seconds=15)
async def eventCheck():
    guild = bot.get_guild(bot.server.serverID)
    currTime = time.strptime(time.ctime(time.time()))
    currHour = currTime.tm_hour
    currMinute = currTime.tm_min

    if bot.server.eventOpen:
        event = bot.server.currEvent
        eventHour = int(event.time[0:2])
        eventMinute = int(event.time[2:4])
        if bot.server.eventStarted:
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 60, event.duration):
                bot.server.eventEndAttendance = bot.server.eventVoiceChannel.members.copy()
                fullAttendance = []
                partialAttendance = []

                for memberStart in bot.server.eventStartAttendance:
                    if any(memberStart.id == memberEnd.id for memberEnd in bot.server.eventEndAttendance):
                        fullAttendance.append(memberStart)
                    else:
                        partialAttendance.append(memberStart)
                
                for member in fullAttendance:
                    bot.server.giveDKP(member, event.dkp)
                bot.server.saveUserFile()

                #Display message of members who attended and got dkp, and list of member who showed up late or left early
                channel = guild.get_channel(bot.server.dkpChannel)
                fullResponse = "**Full Attendance list**:\n" + "\n".join([f"`{member.nick}`" for member in fullAttendance])
                partialResponse = "**partial Attendance list**:\n" + "\n".join([f"`{member.nick}`" for member in partialAttendance])
                await channel.send(f"{fullResponse}")
                await channel.send(f"{partialResponse}")
                

                await bot.server.eventVoiceChannel.delete()
                bot.server.eventVoiceChannel = None
                bot.server.eventStartAttendance = []
                bot.server.eventEndAttendance = []
                bot.server.eventVoiceChannel = None
                bot.server.eventStarted = False
                bot.server.eventOpen = False
        else:
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 5, 0):
                bot.server.eventStarted = True
                bot.server.eventStartAttendance = bot.server.eventVoiceChannel.members.copy()
                await bot.server.eventVoiceChannel.send("attendance has started, leaving early will result in no dkp")
    else:
        for event in bot.server.events:
            eventHour = int(event.time[0:2])
            eventMinute = int(event.time[2:4])
            if withinTimeRange(currHour, currMinute, eventHour, eventMinute, 0, -5):
                bot.server.eventOpen = True
                bot.server.currEvent = event
                bot.server.eventVoiceChannel = await guild.create_voice_channel(name=bot.server.currEvent.name)
                await bot.server.eventVoiceChannel.send("Join for event. Event starts in 5 minutes")

with open("API-Key.txt", "r", encoding='utf-8-sig') as f:
    apiKey = f.read()
    f.close()

bot.run(apiKey)