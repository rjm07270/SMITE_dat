import discord
from discord.utils import find
from discord.ext import commands
from db import db

command_attrs = {'hidden':True}
class events(commands.Cog, name='events', command_attrs=command_attrs):
    """description of class"""
    #Handles anything to do with events
    def __init__(self,client):
        self.client=client
        
    #Event: joined new discord server
    @commands.Cog.listener()
    async def on_guild_join(self,guild):    
        #checking server list for setting
        if guild.id in db.perms_cache:
            del db.perms_cache[guild.id]
        try:
            #removes all all setting from db apone rejoin
            
            sql= ("DROP TABLE discord_"+str(guild.id))
            await db.exicute(db.conn,sql)
        except:            
            pass
        try:
            sql= "DELETE FROM discord_servers WHERE discord_server= '"+str(guild.id)+"'"
            await db.exicute(db.conn,sql)
        except:
            pass
            
        #makes the tables full of server setting
        sql = ("CREATE TABLE discord_"+str(guild.id) + " ("+
        "white_list_users VARCHAR(18), black_list_users VARCHAR(18),"+
        " white_list_ch VARCHAR(18), black_list_ch VARCHAR(18),"+
        " admins VARCHAR(18), DJs VARCHAR(18),"+
        " allow_roll varchar(32)"
        +")")
        await db.insert(db.conn,sql)
        #enters in default values
        sql = ("INSERT INTO discord_"+str(guild.id) + " (white_list_users, black_list_users, white_list_ch, black_list_ch, admins, DJs, allow_roll)" +
        " VALUES('000000000000000000','000000000000000000','000000000000000000','000000000000000000','000000000000000000','000000000000000000','000000000000000000')")
        
        await db.insert(db.conn,sql) 

        sql = "INSERT INTO discord_servers"+" (discord_server, isWhite_ch, isWhite_user, isDJ)values("+str(guild.id)+",False,False,False)"
        
        await db.insert(db.conn,sql)

        

def setup(client):
    client.add_cog(events(client))

