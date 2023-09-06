import discord
from discord.ext import commands


import os
from dotenv import load_dotenv
from db import db
from help import Help
load_dotenv()                                                                   #loads env file in curent directory by default
TOKEN=os.getenv('TOKEN')
cogs = []
def __init__():
    db()
    client = commands.Bot(command_prefix='1!', intents = discord.Intents.all())
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
            print(f'cogs.{filename[:-3]}')
    for i in range(len(cogs)):
        cogs[i].setup(client)
    client.help_command = Help()

    print('Token: '+TOKEN)
    client.run(TOKEN)
__init__()
