import discord
from discord import app_commands
from discord.ext import commands
import random

# Enable Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

bot.rollWindow = False
bot.rollWindowResults = []
userRollCount = {}
rollChannelID = 1298885178562711624; # To prevent rolling in other channels.
roleID = 1300336466660167710 # Limit who can start/stop rolling sessions


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready. Logged in as {bot.user}")

# Dark wants a timer parameter
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
        await interaction.response.send_message(f"@everyone You may begin rolling for: `{item}`")

# Need to track who has extra rolls to use
# Need to add command to give and take extra rolls
# currently everyone can roll twice but thats not ideal
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
        user = interaction.user.name
        if user not in userRollCount:
            userRollCount[user] = 1
            bot.rollWindowResults.append((interaction.user.name, number))
        elif userRollCount[user] < 2:
            userRollCount[user] += 1
            bot.rollWindowResults.append((interaction.user.name, number))
        else:   
            await interaction.followup.send(f"{interaction.user.mention} you have already rolled twice, your {number} will be ignored.")
            #No workie and idk why
            #"Command 'roll' raised an exception: TypeError: object method can't be used in 'await' expression"
            await interaction.delete_original_response()

# Run the bot
bot.run('MTI5ODgzNTIzMDYyMjIyMDI5OQ.G8jnzr.ErBLvOEmw-igeMl6Z46BMNZroU6IDQZ7fqdz_g')
