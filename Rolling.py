import discord
import random
from discord.ext import commands
from discord import app_commands
from Server import Server
from User import User
from Event import Event
from helper import *

class Rolling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setmaxroll", description="Set max # of rolls per open window")
    async def setmaxroll(self, interaction: discord.Interaction, max_roll_count: int):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return    
        
        if max_roll_count < 1:
            await interaction.response.send_message("You can not set a number lower than 1")
            return
        else:
            server.maxRolls = max_roll_count

    @app_commands.command(name="rollwindowopen", description="allows users to roll on items")
    async def rollwindowopen(self, interaction: discord.Interaction, item: str, trait: str):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return

        if server.rollWindow == True:
            await interaction.response.send_message("Rolling is already in progress")
        else:   
            server.rollWindow = True
            server.rollWindowResults = []
            server.userRollCount = {}
            await interaction.response.send_message(f"@here You may begin rolling for: `{item} - {trait}` ")

    @app_commands.command(name="rollwindowclose", description="Stop all rolling. List winner")
    async def rollwindowclose(self, interaction: discord.Interaction):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        
        if server.rollWindow == False:
            await interaction.response.send_message("Rolling is already closed")
        elif not server.rollWindowResults:   
            await interaction.response.send_message("Roll window closed - No rolls logged")
        else:   
            sortedResult = sorted(server.rollWindowResults, key=lambda x: x[1], reverse=True)
            await interaction.response.send_message("\n".join([f"`{name}: {number}`" for name, number in sortedResult]))
        server.rollWindow = False

    @app_commands.command(name="roll", description="Rolls a number between 1 and 100")
    async def roll(self, interaction: discord.Interaction):
        server = self.bot.server
        if not await server.validChannel(interaction):
            return

        number = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 You rolled a {number}! 🎲")

        if server.rollWindow == True:
            interName = interaction.user.name
            interNick = interaction.user.nick if interaction.user.nick != None else interName
            interID = interaction.user.id
            maxRolls = server.maxRolls

            user = server.findUser(interID)
            if user != None:
                user.updateUser(user.id, interNick, interName, user.extraRolls, user.dkp)

            if interID not in server.userRollCount:
                server.userRollCount[interID] = 1
                server.rollWindowResults.append((interNick, number))
            elif user == None or user.extraRolls == 0:
                await interaction.followup.send(f"{interaction.user.mention} you have no extra rolls avalible")
                await interaction.delete_original_response()
            elif server.userRollCount[user.id] < server.maxRolls and user.extraRolls > 0:
                server.userRollCount[user.id] += 1
                user.extraRolls -= 1
                server.rollWindowResults.append((interNick, number))
            else:   
                await interaction.followup.send(f"{interaction.user.mention} you have already rolled {maxRolls} times(s), your {number} will be ignored.")
                await interaction.delete_original_response()

        server.saveUserFile()

    @app_commands.command(name="addroll", description="Gives a user an extra roll to use later")
    async def addroll(self, interaction: discord.Interaction, member: discord.Member):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        
        user = server.findUser(member.id)
        if user == None:
            user = User(member.id, member.nick, member.name, 0, 0)
            server.users.append(user)
        
        user.extraRolls += 1
        server.saveUserFile()
        await interaction.response.send_message(f"{user.nickName} has been given an extra roll.")

    @app_commands.command(name="removeroll", description="Removes an extra roll from a user if they have one")
    async def removeroll(self, interaction: discord.Interaction, member: discord.Member):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        user = server.findUser(member.id)   

        if user == None or user.extraRolls == 0:
            await interaction.response.send_message(f"{member.name} has no extra rolls.")
        else:
            await interaction.response.send_message(f"{member.name} has had an extra roll taken away.")
            user.extraRolls -= 1
        server.saveUserFile()

    @app_commands.command(name="extrarolls", description="How many extra rolls you have.")
    async def extrarolls(self, interaction: discord.Interaction):
        server = self.bot.server
        if not await server.validChannel(interaction):
            return
        
        user = server.findUser(interaction.user.id)
        await interaction.response.send_message(f"You have {0 if user == None else user.extraRolls} extra roll(s)")

    @app_commands.command(name="extrarollsearch", description="How many extra rolls someone else has.")
    async def extrarollsearch(self, interaction: discord.Interaction, member: discord.Member):
        server = self.bot.server
        if not await server.validChannel(interaction) and not await server.validRole(interaction):
            return
        
        user = server.findUser(member.id)
        await interaction.response.send_message(f"{member.name} has {0 if user == None else user.extraRolls} extra roll(s)")

    @app_commands.command(name="extrarolltable", description="Table of users extra rolls. Users with none may not appear.")
    async def extrarolltable(self, interaction: discord.Interaction, rows: int):
        server = self.bot.server
        if not await server.validChannel(interaction) and not await server.validRole(interaction):
            return
        sortedUsers = sorted(server.users, key=lambda x: x.extraRolls, reverse=True)
        if len(sortedUsers) == 0:
            response = "Nobody has any extra rolls."
        else:
            response = "\n".join([f"`Name: {user.nickName}, Extra rolls: {user.extraRolls}`" for user in sortedUsers[0:rows]])
        await interaction.response.send_message(f"{response}")