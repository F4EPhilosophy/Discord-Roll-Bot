from helper import *
import discord
from discord.ext import commands
from discord import app_commands

class DKP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="adddkp", description="Gives player dkp")
    async def adddkp(self, interaction: discord.Interaction, member: discord.Member, dkp_amount: int):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        
        server.giveDKP(member, -1*dkp_amount)
        server.saveUserFile()

        await interaction.response.send_message(f"{member.name} has had {dkp_amount} DKP added.")

    @app_commands.command(name="removedkp", description="Removes player dkp")
    async def removedkp(self, interaction: discord.Interaction, member: discord.Member, dkp_amount: int):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        
        server.giveDKP(member, -1*dkp_amount)
        server.saveUserFile()
        
        await interaction.response.send_message(f"{member.name} has had {dkp_amount} DKP removed.")

    @app_commands.command(name="setdkpchannel", description="Set the channel dkp related text will appear.")
    async def setdkpchannel(self, interaction: discord.Interaction):
        server = self.bot.server
        if not await server.validRole(interaction):
            return
        
        server.dkpChannel = interaction.channel.id
        server.saveConfig()
        await interaction.response.send_message("Channel Set")

    @app_commands.command(name="createlisting", description="Creates a thread for item listing.")
    async def createlisting(self, interaction: discord.Interaction, item: str, trait: str):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        
        starter_message = await interaction.channel.send(f"Listing for **{item}** with **{trait}** has been created.")
        await starter_message.create_thread(name = f"{item} - {trait}", auto_archive_duration = 1440)

    @app_commands.command(name="maxdkp", description="set max dkp.")
    async def maxdkp(self, interaction: discord.Interaction, max: int, wipe: bool):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        server.maxdkp = max

        if wipe:
            for user in server.users:
                user.dkp = clamp(user.dkp, server.mindkp, server.maxdkp)

        await interaction.response.send_message(f"Max DKP has been set to {server.maxdkp}")

    @app_commands.command(name="mindkp", description="set min dkp")
    async def mindkp(self, interaction: discord.Interaction, min: int, wipe: bool):
        server = self.bot.server
        if not await server.validChannel(interaction) or not await server.validRole(interaction):
            return
        server.mindkp = min

        if wipe:
            for user in server.users:
                user.dkp = clamp(user.dkp, server.mindkp, server.maxdkp)

        await interaction.response.send_message(f"Min DKP has been set to {server.mindkp}")

    @app_commands.command(name="mydkp", description="Check how much DKP you have.")
    async def mydkp(self, interaction: discord.Interaction):
        server = self.bot.server
    
        user = server.findUser(interaction.user.id)
        channel = await interaction.user.create_dm()

        await channel.send(f"You have {user.dkp} DKP")

    @app_commands.command(name="dkpsearch", description="search specific users dkp.")
    async def dkpsearch(self, interaction: discord.Interaction, member: discord.Member):
        server = self.bot.server
        if not server.validRole(interaction):
            return
        
        channel = await interaction.user.create_dm()
        user = server.findUser(member.id)
        
        await channel.send(f"{member.name} has {0 if user == None else user.dkp} dkp")

    @app_commands.command(name="dkptable", description="Print table of DKP")
    async def tabledkp(self, interaction: discord.Interaction, rows: int):
        server = self.bot.server
        if not await server.validRole(interaction):
            return
        
        channel = await interaction.user.create_dm()
        sortedUsers = sorted(server.users, key=lambda x: x.dkp, reverse=True)

        if len(sortedUsers) == 0:
            response = "No users in dkp list. Maybe no one has dkp?"
        else:
            response = "\n".join([f"`Name: {user.nickName}, DKP: {user.dkp}`" for user in sortedUsers[0:rows]])
        await channel.send(f"{response}")

    @app_commands.command(name="dkpgiveall", description="Give dkp to everyone in voice channel")
    async def dkpgiveall(self, interaction: discord.Interaction, channel_id: str, dkp_amount: int):
        server = self.bot.server
        guild = self.bot.get_guild(server.serverID)
        channel = guild.get_channel(int(channel_id))

        for member in channel.members:
            server.giveDKP(member, dkp_amount)
        server.saveUserFile()

        await interaction.response.send_message(f'DKP granted')