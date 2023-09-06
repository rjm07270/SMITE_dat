from discord.ext import commands
from db import db

command_attrs = {'hidden':True}
class perms(commands.Cog, name='perms', command_attrs=command_attrs):
    """description of class"""
    
    def __init__(self,client):
        self.client=client

    @commands.command(help="It works")
    async def white_user(self, ctx):
        
        value=None
        if(bool(db.perms_cache[ctx.guild.id]["isWhite_user"][len(db.perms_cache[ctx.guild.id]["isWhite_user"])-1])):
            value=0
            db.perms_cache[ctx.guild.id]["isWhite_user"].remove(1)
        else:
            value=1
            db.perms_cache[ctx.guild.id]["isWhite_user"].remove(0)

        db.perms_cache[ctx.guild.id]["isWhite_user"].append(value)
        sql = "UPDATE discord_servers SET isWhite_ch= "+value+" WHERE discord_server = "+str(ctx.guild.id)
        
        await db.insert(db.conn,sql)

        await ctx.send(""+str(bool(db.perms_cache[ctx.guild.id]["isWhite_user"][len(db.perms_cache[ctx.guild.id]["isWhite_user"])-1])))
    @commands.command()
    async def white_ch(self, ctx):
        
            value=None
            if(bool(db.perms_cache[ctx.guild.id]["isWhite_ch"][len(db.perms_cache[ctx.guild.id]["isWhite_ch"])-1])):
                value=0
                db.perms_cache[ctx.guild.id]["isWhite_ch"].remove(1)
            else:
                value=1
                db.perms_cache[ctx.guild.id]["isWhite_ch"].remove(0)

            db.perms_cache[ctx.guild.id]["isWhite_ch"].append(value)
            sql = "UPDATE discord_servers SET isWhite_ch= "+value+" WHERE discord_server = "+str(ctx.guild.id)
            
            await db.insert(db.conn,sql)

            await ctx.send(""+str(bool(db.perms_cache[ctx.guild.id]["isWhite_ch"][len(db.perms_cache[ctx.guild.id]["isWhite_ch"])-1])))


    @commands.command()
    async def black(self, ctx, input):
        
            black_id=None
            input =input[2:-1]
            flag=False
            sql=None
            #channel checks
            for channel in ctx.guild.channels:
                if str(channel.id) == input:
                    black_id = input
            if not black_id==None:
                flag=True
                
                if(black_id in db.perms_cache[ctx.guild.id]["black_list_ch"]):
                    sql = "DELETE FROM discord_"+str(ctx.guild.id)+" WHERE black_list_ch = %s"
                    db.perms_cache[ctx.guild.id]["black_list_ch"].remove(str(black_id))
                    await ctx.send("Deleted Channel from black list")
                else:
                    sql = "INSERT INTO discord_"+str(ctx.guild.id)+"(black_list_ch) VALUES(%s)"
                    db.perms_cache[ctx.guild.id]["black_list_ch"].append(str(black_id))
                    await ctx.send("Added Channel to black list")
            #user checks
            for user in ctx.guild.members: 
                if str(user.id) == input:
                    black_id = input
            
            if (not black_id==None and not flag):
                
                if(black_id in db.perms_cache[ctx.guild.id]["black_list_users"]):
                    sql = "DELETE FROM discord_"+str(ctx.guild.id)+" WHERE black_list_users = %s"
                    db.perms_cache[ctx.guild.id]["black_list_users"].remove(str(black_id))
                    await ctx.send("Deleted User from black list")
                else:
                    sql = "INSERT INTO discord_"+str(ctx.guild.id)+"(black_list_users) VALUES(%s)"
                    db.perms_cache[ctx.guild.id]["black_list_users"].append(str(black_id))
                    await ctx.send("Added User to black list")
            #enters into db    
            if not black_id==None:
                value= (black_id,)
                sql=sql.replace("%s", value) 
                await db.insert(db.conn,sql)

    @commands.command()
    async def white(self, ctx, input):
            black_id=None
            input =input[2:-1]
            flag=False
            sql=None
            #channel checks
            for channel in ctx.guild.channels:
                if str(channel.id) == input:
                    black_id = input
            if not black_id==None:
                flag=True
                
                if(black_id in db.perms_cache[ctx.guild.id]["white_list_ch"]):
                    sql = "DELETE FROM discord_"+str(ctx.guild.id)+" WHERE white_list_ch = %s"
                    db.perms_cache[ctx.guild.id]["white_list_ch"].remove(str(black_id))
                    await ctx.send("Deleted Channel from white list")
                else:
                    sql = "exicute INTO discord_"+str(ctx.guild.id)+"(white_list_ch) VALUES(%s)"
                    db.perms_cache[ctx.guild.id]["white_list_ch"].append(str(black_id))
                    await ctx.send("Added Channel to white list")
            #user checks
            for user in ctx.guild.members: 
                if str(user.id) == input:
                    black_id = input
            
            if (not black_id==None and not flag):
                
                if(black_id in db.perms_cache[ctx.guild.id]["white_list_users"]):
                    sql = "DELETE FROM discord_"+str(ctx.guild.id)+" WHERE white_list_users = %s"
                    db.perms_cache[ctx.guild.id]["white_list_users"].remove(str(black_id))
                    await ctx.send("Deleted User from white list")
                else:
                    sql = "INSERT INTO discord_"+str(ctx.guild.id)+"(white_list_users) VALUES(%s)"
                    db.perms_cache[ctx.guild.id]["white_list_users"].append(str(black_id))
                    await ctx.send("Added User to white list")
            #enters into db    
            if not black_id==None:
                value= (black_id,)
                sql=sql.replace("%s", value)
                await db.insert(db.conn,sql,value)
    
                
    async def cog_check(self, ctx):
        return await db.perms_check(db,ctx)

def setup(client):
    client.add_cog(perms(client))


