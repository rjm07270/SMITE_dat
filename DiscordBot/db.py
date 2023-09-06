#import mysql.connector
#from mysql.connector import Error
import sqlite3
from sqlite3 import Error
import os


class db(object):
    """description of class"""
    #class is for connecting to the database

    conn=None
    @classmethod
    def __init__(cls):
        
        cls.conn = sqlite3.connect('music.db')
        
        cls.perms_cache={}

    @classmethod    
    async def exicute(conn,sql):
        cursor=conn.cursor()
        try:
            cursor.execute(sql)
            conn.commit
        except Error as e:
            print("Error: "+str(e))

    async def get(conn,sql):
        dic={}
        
        cursor=conn.cursor()
        try:
            cursor.execute(sql)
        except Error as e:
            print("Error: "+str(e))
            return None                
        count=0
        for x in cursor:                  #puts all values in a dichanrary based on your select statment does not work for select all "*"
            parts=sql.split(" ")
            key=parts.pop(1)
            i=0
            while(not key=="FROM"):     #cuts off the ch
                if key[-1]==",":
                    key=key[0:-1]
                if key in dic:
                    dic[key].append(x[i])
                else:
                    dic[key]=[x[i]]
                key=parts.pop(1)
                i=i+1
        return dic
        
    async def insert(conn,sql):
        cursor=conn.cursor()               
        try:
            cursor.execute(sql)
            conn.commit()
            
        except Error as e:
            print("Error: "+str(e))


    async def perms_check(cls,ctx, DJ=False):

        perms_cache = cls.perms_cache
        id = ctx.message.guild.id
        user= str(ctx.message.author.id)
        #loads cache for servers as needed
        if not id in perms_cache:                               
            sql = ("SELECT white_list_users, black_list_users, white_list_ch, black_list_ch, admins, DJs, allow_roll FROM discord_"+str(id))
            perms_cache[id] = await cls.get(cls.conn, sql)
                
            sql = "SELECT isWhite_ch, isWhite_user, isDJ FROM discord_servers"
            temp =await cls.get(cls.conn,sql)
            for key in temp.keys():
                perms_cache[id][key]=temp[key]
        #So the owner cant ban himself or screw anything up
        if(ctx.guild is not None and ctx.guild.owner_id == ctx.author.id):
            return True
        #sees if the text channel is authorized
        if bool(perms_cache[id]["isWhite_ch"][len(perms_cache[id]["isWhite_ch"])-1]):
            if str(ctx.channel.id) in perms_cache[id]["white_list_ch"]:
                if(not ((user in perms_cache[id]["white_list_users"] and bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1])) or (not user in perms_cache[id]["black_list_users"] and not bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1])))):
                    await ctx.send("You are not allowed to use this command")
                    return False
                return True
            await ctx.send("Permission Denied")
            return False
        if not str(ctx.channel.id) in perms_cache[id]["black_list_ch"] and not perms_cache[id]["isWhite_ch"][len(perms_cache[id]["isWhite_ch"])-1]:
            print (not ((user in perms_cache[id]["white_list_users"] and bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1])) or (not user in perms_cache[id]["black_list_users"] and not bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1]))))
            if(not ((user in perms_cache[id]["white_list_users"] and bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1])) or (not user in perms_cache[id]["black_list_users"] and not bool(perms_cache[id]["isWhite_user"][len(perms_cache[id]["isWhite_user"])-1])))):
                await ctx.send("You are not allowed to use this command")
                return False
            return True   
        
        await ctx.send("Wrong Channel")
        return False
        
        #this is code need to be added in so the owner will alwasys have perms on the server    
        
        


  


