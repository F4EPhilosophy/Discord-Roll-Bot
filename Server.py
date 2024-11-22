from User import User
import configparser
import os
import discord
from Event import Event
from helper import *

class Server:
    serverID = 1298885178080497717
    users = []
    events = []
    rollsFileName = "extraRolls.txt"
    configFileName = "config.ini"
    eventsFileName = "events.txt"
    roleID = -1
    rollChannelID = -1
    dkpChannel = -1
    userRollCount = {}
    rollWindow = False
    rollWindowResults = []
    eventOpen = False
    eventStarted = False
    currEvent = None
    eventVoiceChannel = None
    eventStartAttendance = []
    eventEndAttendance = []
    maxdkp = 0
    mindkp = 0
    maxRolls = 1

    def __init__(self):
        self.getConfig()
        self.getUserFile()
        self.getEventSchedule()
    
    def findUser(self, id):
        for user in self.users:
            if user.id == id:
                return user
        return None
    
    def getUserFile(self):
        self.users = []
        if os.path.exists(self.rollsFileName):
            with open(self.rollsFileName, "r", encoding='utf-8-sig') as f:
                for line in f:
                    vals = line.split(',')
                    id = int(vals[0])
                    nickName = vals[1]
                    discordName = vals[2]
                    extraRolls = int(vals[3])
                    dkp = int(vals[4])
                    self.users.append(User(id, nickName, discordName, extraRolls, dkp))
                f.close()
        else:
            with open(self.rollsFileName, "w", encoding='utf-8-sig') as f:
                f.close()

    def saveUserFile(self, filename=rollsFileName):
        with open(filename, "w", encoding='utf-8-sig') as f:
            for user in self.users:
                f.write(user.formatForFile())
            f.close()

    def getConfig(self):
        config = configparser.ConfigParser()
        if not os.path.exists(self.configFileName):
            config['General'] = {'Role_ID': 0, 'Roll_Channel': 0, 'dkp_Channel': 0}

            with open(self.configFileName, 'x') as configfile:
                config.write(configfile)
                self.roleID = 0
                self.rollChannelID = 0
                self.dkpChannel = 0
        else:
            config.read(self.configFileName)
            self.rollChannelID = config.getint('General', 'Roll_Channel')
            self.roleID = config.getint('General', 'Role_ID')
            self.dkpChannel = config.getint('General', 'dkp_Channel')
    
    def saveConfig(self):
        config = configparser.ConfigParser()
        config.read(self.configFileName)
        config.set('General', 'Roll_Channel', str(self.rollChannelID))
        config.set('General', 'Role_ID', str(self.roleID))
        config.set('General', 'dkp_Channel', str(self.dkpChannel))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def saveEventSchedule(self):
        with open(self.eventsFileName, "w", encoding='utf-8-sig') as f:
            for event in self.events:
                f.write(event.formatForFile())
            f.close()

    def getEventSchedule(self):
        self.events = []
        if os.path.exists(self.eventsFileName):
            with open(self.eventsFileName, "r", encoding='utf-8-sig') as f:
                for line in f:
                    vals = line.split(',')
                    time = vals[0]
                    duration = int(vals[1])
                    name = vals[2]
                    dkp = int(vals[3])
                    recurring = True if vals[4] == 'True' else False
                    self.events.append(Event(time, duration, name, dkp, recurring))
                f.close()
        else:
            with open(self.eventsFileName, "w", encoding='utf-8-sig') as f:
                f.close()

    def giveDKP(self, member, dkp_amount):
        user = self.findUser(member.id)
        if user == None:
            user = User(member.id, member.nick, member.name, 0, 0)
            self.users.append(user)
        user.dkp = user.dkp = clamp(user.dkp + dkp_amount, self.mindkp, self.maxdkp)
        
    async def validChannel(self, interaction: discord.Interaction):
        if interaction.channel.id != self.rollChannelID:
            await interaction.response.send_message("You can not use that command in this channel")
            return False
        return True

    async def validRole(self, interaction: discord.Interaction):
        if not any(role.id == self.roleID for role in interaction.user.roles):
            await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command")
            return False
        return True