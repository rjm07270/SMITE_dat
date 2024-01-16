import re

from discord.ext import commands
from ...SMITE_dat.db import db
from ...SMITE_dat import SMITE

class SMITECommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.users  = {}
        
        
    @commands.command()
    async def get_god_info(self, ctx, god_name: str):
        # Implement the logic to fetch information about a specific god from the SMITE API
        response = f"Information about {god_name}"
        await ctx.send(response)

    @commands.command()
    async def predict_winner(self, ctx, team_info: str):
        # Implement the logic to predict the winner based on team information
        # This could be complex, involving interaction with your AI model
        prediction = f"Predicted winner based on team: {team_info}"
        await ctx.send(prediction)

    @commands.command()
    async def link_smite_account(self, ctx, smite_username: str):
        # Logic to store the Discord user ID and the SMITE username association
        discord_user_id = ctx.author.id
        # Store the mapping in a database or a file
        # For example: {discord_user_id: smite_username}
        self.users[discord_user_id]=SmiteUser(discord_user_id,smite_username)
        response = f"Linked SMITE account '{smite_username}' with Discord user {ctx.author.name}"
        
        await ctx.send(response)


def setup(client):
    client.add_cog(SMITECommands(client))
    
class SmiteUser():
    def __init__(self,discord_user_id,smite_username):
        test = self.check_smite_username(self, smite_username)
        print("Is the username vaild this will display name: "+test)
        sql = f"INSERT INTO discord_smite_link (discord_id, smite_username) VALUES ({discord_user_id}, '{smite_username}')"
        db.insert(sql)
        self.discord_user_id
        
    def check_smite_username(self, smite_username):
        pattern = r'^[A-Za-z0-9](?:[A-Za-z0-9]|_(?=[A-Za-z0-9])){2,28}[A-Za-z0-9]$'
        return re.match(pattern, smite_username) is not None