import discord
from discord.ext import commands
import random
from discord import app_commands

def findUser(id):
    global users
    for user in users:
        if user.id == id:
            return user
    return None

async def validChannel(interaction: discord.Interaction):
    global rollChannelID
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You can not use that command in this channel")
        return False
    return True

async def validRole(interaction: discord.Interaction):
    if not any(role.id == roleID for role in interaction.user.roles):
        await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command")
        return False
    return True

def saveUserFile():
    global users
    with open("extraRolls.txt", "w", encoding='utf-8-sig') as f:
        for user in users:
            f.write(user.formatForFile())
        f.close()

def readUserFile():
    global users 
    users = []
    try:
        with open("extraRolls.txt", "r", encoding='utf-8-sig') as f:
            for line in f:
                vals = line.split(',')
                users.append(User(int(vals[0]), vals[1], vals[2], int(vals[3])))
            f.close()
    except:
        with open("extraRolls.txt", "w", encoding='utf-8-sig') as f:
            f.close()

class User:
    id = -1
    nickName = ""
    discordName = ""
    extraRolls = 0

    def __init__(self, id, nickName, discordName, extraRolls):
        self.updateUser(id, nickName, discordName, extraRolls)

    def formatForFile(self):
        string = str(self.id) + "," + self.nickName + "," + self.discordName + "," + str(self.extraRolls) + "\n"
        return string
    
    def updateUser(self, id, nickName, discordName, extraRolls):
        self.id = id
        self.nickName = nickName if nickName != None else discordName
        self.discordName = discordName
        self.extraRolls = extraRolls


# Enable Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents, allowed_mentions=discord.AllowedMentions(everyone=True) )

users = []

bot.rollWindow = False
bot.rollWindowResults = []
userRollCount = {}
rollChannelID = 1298885178562711624; # To prevent rolling in other channels.
roleID = 1300336466660167710 # Limit who can start/stop rolling sessions

readUserFile()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="rollwindowopen", description="Time to roll!")
async def rollwindowopen(interaction: discord.Interaction, item: str):
    global userRollCount
    if not await validChannel(interaction) or not await validRole(interaction):
        return

    if bot.rollWindow == True:
        await interaction.response.send_message("Rolling is already in progress")
    else:   
        bot.rollWindow = True
        bot.rollWindowResults = []
        userRollCount = {}
        await interaction.response.send_message(f"@here You may begin rolling for: `{item}`")

@bot.tree.command(name="rollwindowclose", description="Stop all rolling.")
async def rollwindowclose(interaction: discord.Interaction):
    if not await validChannel(interaction) or not await validRole(interaction):
        return
    
    if bot.rollWindow == False:
        await interaction.response.send_message("Rolling is already closed")
    else:   
        bot.rollWindow = False
        sortedResult = sorted(bot.rollWindowResults, key=lambda x: x[1], reverse=True)
        await interaction.response.send_message("\n".join([f"`{name}: {number}`" for name, number in sortedResult]))

@bot.tree.command(name="roll", description="Rolls a number between 1 and 100")
async def roll(interaction: discord.Interaction):
    if not await validChannel(interaction):
        return

    number = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 You rolled a {number}! 🎲")

    if bot.rollWindow == True:
        interName = interaction.user.name
        interNick = interaction.user.nick if interaction.user.nick != None else interName
        interID = interaction.user.id

        user = findUser(interID)
        if user != None:
            user.updateUser(user.id, interNick, interName, user.extraRolls)

        if interID not in userRollCount:
            userRollCount[interID] = 1
            bot.rollWindowResults.append((interNick, number))
        elif user == None or user.extraRolls == 0:
            await interaction.followup.send(f"{interaction.user.mention} you have no extra rolls avalible")
            await interaction.delete_original_response()
        elif userRollCount[user.id] < 2 and user.extraRolls > 0:
            userRollCount[user.id] += 1
            user.extraRolls -= 1
            bot.rollWindowResults.append((interNick, number))
        else:   
            await interaction.followup.send(f"{interaction.user.mention} you have already rolled twice, your {number} will be ignored.")
            await interaction.delete_original_response()

    saveUserFile()

@bot.tree.command(name="addroll", description="Gives a user an extra roll to use later")
async def addroll(interaction: discord.Interaction, member: discord.Member):
    global users
    if not await validChannel(interaction) or not await validRole(interaction):
        return
    
    user = findUser(member.id)
    if user == None:
        user = User(member.id, member.nick, member.name, 0)
        users.append(user)
    
    user.extraRolls += 1
    saveUserFile()
    await interaction.response.send_message(f"{user.nickName} has been given an extra roll.")

@bot.tree.command(name="removeroll", description="Removes an extra roll from a user if they have one")
async def removeroll(interaction: discord.Interaction, member: discord.Member):
    if not await validChannel(interaction) or not await validRole(interaction):
        return
    user = findUser(member.id)   

    if user == None or user.extraRolls == 0:
        await interaction.response.send_message(f"{member.name} has no extra rolls.")
    else:
        await interaction.response.send_message(f"{member.name} has had an extra roll taken away.")
        user.extraRolls -= 1
    saveUserFile()

@bot.tree.command(name="extrarolls", description="How many extra rolls you have.")
async def extrarolls(interaction: discord.Interaction):
    if not await validChannel(interaction):
        return
    
    user = findUser(interaction.user.id)
    await interaction.response.send_message(f"You have {0 if user == None else user.extraRolls} extra roll(s)")

@bot.tree.command(name="extrarollsearch", description="How many extra rolls someone else has.")
async def extrarollsearch(interaction: discord.Interaction, member: discord.Member):
    if not await validChannel(interaction) and not await validRole(interaction):
        return
    
    user = findUser(member.id)
    await interaction.response.send_message(f"{member.name} has {0 if user == None else user.extraRolls} extra roll(s)")

@bot.tree.command(name="extrarolltable", description="Table of users extra rolls. Users with none may not appear.")
async def extrarolltable(interaction: discord.Interaction, rows: int):
    if not await validChannel(interaction) and not await validRole(interaction):
        return
    sortedUsers = sorted(users, key=lambda x: x.extraRolls, reverse=True)
    if len(sortedUsers) == 0:
        response = "Nobody has any extra rolls."
    else:
        response = "\n".join([f"`Name: {user.nickName}, Extra rolls: {user.extraRolls}`" for user in sortedUsers[0:rows]])
    await interaction.response.send_message(f"{response}")

@bot.tree.command(name="setrollchannel", description="Designates role channel to channel command is used in.")
async def setrollchannel(interaction: discord.Interaction):
    global rollChannelID
    rollChannelID = interaction.channel.id

@bot.tree.command(name="setrollrole", description="Sets role for permissions to open/close roll windows.")
async def setrollrole(interaction: discord.Interaction, id: str):
    global roleID
    roleID = int(id)

# Run the bot.

with open("API-Key.txt", "r", encoding='utf-8-sig') as f:
    apiKey = f.read()
    f.close()

bot.run(apiKey)