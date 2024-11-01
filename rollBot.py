import discord
from discord import app_commands
from discord.ext import commands
import random
import sqlite3

# Enable Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

try:
    sqliteConnection = sqlite3.connect('extraRolls.sql')
    cursor = sqliteConnection.cursor()
    print('Connected to the database')
    cursor.execute("""CREATE TABLE IF NOT EXISTS user (
                    name TEXT,
                    rolls INTEGER,
                    ID INTEGER
                   )""")
    sqliteConnection.commit()
    sqliteConnection.close()

except:
    print('Failed to connect to the database')

bot.rollWindow = False
bot.rollWindowResults = []
userRollCount = {}
rollChannelID = 1298885178562711624; # To prevent rolling in other channels.
roleID = 1300336466660167710 # Limit who can start/stop rolling sessions

#Add logic to backup the database every 24 hours

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="rollwindowopen", description="Time to roll!")
async def rollwindowopen(interaction: discord.Interaction, item: str):
    global userRollCount
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You can not use that command in this channel")
    elif not any(role.id == roleID for role in interaction.user.roles):
        await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command")
    elif bot.rollWindow == True:
        await interaction.response.send_message("Rolling is already in progress")
    else:   
        bot.rollWindow = True
        bot.rollWindowResults = []
        userRollCount = {}
        await interaction.response.send_message(f"@here You may begin rolling for: `{item}`")

@bot.tree.command(name="rollwindowclose", description="Stop all rolling.")
async def rollwindowclose(interaction: discord.Interaction):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel")
    elif not any(role.id == roleID for role in interaction.user.roles):
         await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command")
    elif bot.rollWindow == False:
        await interaction.response.send_message("Rolling is already closed")
    else:   
        bot.rollWindow = False
        sortedResult = sorted(bot.rollWindowResults, key=lambda x: x[1], reverse=True)
        await interaction.response.send_message("\n".join([f"`{name}: {number}`" for name, number in sortedResult]))

@bot.tree.command(name="roll", description="Rolls a number between 1 and 100")
async def roll(interaction: discord.Interaction):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot roll in this channel")
        return

    number = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 You rolled a {number}! 🎲")

    if bot.rollWindow == True:
        user = interaction.user.id
        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()
        cursor.execute("SELECT rolls FROM user WHERE id = ?", (interaction.user.id,))
        userData = cursor.fetchone()

        if user not in userRollCount:
            userRollCount[user] = 1
            bot.rollWindowResults.append((interaction.user.name, number))
        elif userData == None or userData[0] == 0:
            await interaction.followup.send(f"{interaction.user.mention} you have no extra rolls avalible")
            await interaction.delete_original_response()
        elif userRollCount[user] < 2 and userData[0] >= 1:
            userRollCount[user] += 1
            cursor.execute("UPDATE user SET rolls = rolls - 1 WHERE id = ?", (interaction.user.id,))
            bot.rollWindowResults.append((interaction.user.name, number))
        
        else:   
            await interaction.followup.send(f"{interaction.user.mention} you have already rolled twice, your {number} will be ignored.")
            await interaction.delete_original_response()

        sqliteConnection.commit()
        sqliteConnection.close()

@bot.tree.command(name="addroll", description="Gives a user an extra roll to use later")
async def addroll(interaction: discord.Interaction, member: discord.Member):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel")
    elif not any(role.id == roleID for role in interaction.user.roles):
        await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command")
    else:   
        userID = member.id

        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()
        

        cursor.execute("""SELECT 1 FROM user WHERE id = ?""", (userID,))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("""INSERT INTO user (name, rolls, ID) VALUES (?, ?, ?)""", (member.name, 1, userID))
            await interaction.response.send_message(f"{member.name} has been given an extra roll.")
            sqliteConnection.commit()
            sqliteConnection.close()
        else:   
            cursor.execute("""UPDATE user SET rolls = rolls + 1 WHERE ID = ?""", (userID,))
            await interaction.response.send_message(f"{member.name} has been given an extra roll.")
            sqliteConnection.commit()
            sqliteConnection.close()

@bot.tree.command(name="removeroll", description="Removes an extra roll from a user if they have one")
async def removeroll(interaction: discord.Interaction, member: discord.Member):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel.")
    elif not any(role.id == roleID for role in interaction.user.roles):
        await interaction.response.send_message(f"{interaction.user.mention} you do not have permission to use this command.")
    else:   
        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()

        cursor.execute("SELECT rolls FROM user WHERE id = ?", (member.id,))
        userData = cursor.fetchone()

        if not userData:
            await interaction.response.send_message(f"{member.name} does not exist in the database.")
        elif userData[0] == 0:
            await interaction.response.send_message(f"{member.name} has no extra rolls.")
        else:
            cursor.execute("UPDATE user SET rolls = rolls - 1 WHERE id = ?", (member.id,))
            await interaction.response.send_message(f"{member.name} has had an extra roll taken away.")
            sqliteConnection.commit()
        sqliteConnection.close()

@bot.tree.command(name="extrarolls", description="Removes an extra roll from a user if they have one")
async def extrarolls(interaction: discord.Interaction):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel.")
    else:
        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()
        cursor.execute("SELECT rolls FROM user WHERE id = ?", (interaction.user.id,))
        userData = cursor.fetchone()
        await interaction.response.send_message(f"You have {userData[0]} extra roll(s)")


@bot.tree.command(name="extrarollsearch", description="Removes an extra roll from a user if they have one")
async def extrarollsearch(interaction: discord.Interaction, member: discord.Member):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel.")
    else:
        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()
        cursor.execute("SELECT rolls FROM user WHERE id = ?", (member.id,))
        userData = cursor.fetchone()
        await interaction.response.send_message(f"{member.name} has {userData[0]} extra roll(s)")

@bot.tree.command(name="extrarolltable", description="Removes an extra roll from a user if they have one")
async def extrarolltable(interaction: discord.Interaction, rows: int):
    if interaction.channel.id != rollChannelID:
        await interaction.response.send_message("You cannot use that command in this channel.")
    else:
        sqliteConnection = sqlite3.connect('extraRolls.sql')
        cursor = sqliteConnection.cursor()

        cursor.execute("SELECT COUNT(*) FROM user")
        totalRows = cursor.fetchone()[0]
        if rows > totalRows:
            rows = totalRows
        
        cursor.execute("SELECT name, rolls FROM user LIMIT ?", (rows,))
        rows = cursor.fetchall()
        if rows:
            sortedTable = sorted(rows, key=lambda x: x[1], reverse=True)
            response = "\n".join([f"`Name: {row[0]}, Extra rolls: {row[1]}`" for row in sortedTable])
        else:
            response = "No data found."
        await interaction.response.send_message(f"{response}")

    sqliteConnection.close()

# Run the bot

with open("API-Key.txt", "r", encoding='utf-8-sig') as f:
    apiKey = f.read()
bot.run(apiKey)
