import discord
from discord.ext import commands
import asyncio
import re
from db import db
from .perms import perms
import os
from threading import Thread

class NoTracksFound(commands.CommandError):
    pass
command_attrs = {'hidden':True}
class music(commands.Cog, name='music', command_attrs=command_attrs):
    def __init__(self, client):
        self.client =client
        self.queues={}
        self.old_queues={}
        self.back=False

    def queue_start(self,ctx,id):
        
        if self.queues[id] != []:
            voice =ctx.guild.voice_client
            source =self.queues[id].pop()
            if id in self.old_queues:
                self.old_queues[id].append(source)
            else:
                self.old_queues[id]=[source]
            player=voice.play(source.source, after=lambda x=None: self.queue_start(ctx,id))
            if self.old_queues[id]==[]:
                 print("del")



    @commands.command()
    async def join(self,ctx):
        
        if ctx.author.voice is None:
            await ctx.send("Get into a channel")
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
        
    @commands.command()
    async def disconnect(self,ctx):
        
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self,ctx,*,args=None):
        song=""
        for x in args:
            song=song+x
        if song!=None:
            if ctx.author.voice is None:
                await ctx.send("Get into a channel")
            else:
                voice_channel = ctx.author.voice.channel
                if ctx.voice_client is None:
                    await voice_channel.connect()

            
            
            source = musicQueue(song)
            await source._init()
            guild_id = ctx.message.guild.id
            voice =ctx.guild.voice_client
            if guild_id in self.queues:
                self.queues[guild_id].append(source)
                await ctx.send("Song added")
            else:
                self.queues[guild_id] = [source]
                self.queue_start(ctx, guild_id)
                await ctx.send("Starting voice chat")                                                                                       
        else:
            ctx.voice_client.resume()
            await ctx.send("unpause")
    
    @commands.command()
    async def pause(self,ctx):
        
        ctx.voice_client.pause()
        await ctx.send("pause")
    

    @commands.command()
    async def stop(self,ctx):
        
        guild_id = ctx.message.guild.id
        self.queues[guild_id] = []
        ctx.voice_client.stop()
        await ctx.send("stopped")
    @commands.command()
    async def skip(self,ctx):
        
        ctx.voice_client.stop()
        await ctx.send("skipped")

    @commands.command()
    async def back(self,ctx):

        id = ctx.message.guild.id
        if len(self.old_queues[id])>0:
            self.queues[id].insert(0,await self.old_queues[id].pop()._init())
            print("back")
            ctx.voice_client.stop()          
        await ctx.send("back")

    @commands.command()
    async def list_songs(self,ctx):
        
        sql=("SELECT name FROM music")
        info = await db.get(db.conn,sql)
        text="List of Songs: "
        print (info)
        for key in info.keys():
            for i in range(0,len(info[key])):
                text=text+"\n"+"     "+info[key][i]
        await ctx.send(text)
    @commands.command()
    async def test(self,ctx):
        sql=("SELECT name, file_loc FROM music")
        info = await db.get(db.conn,sql)
        
        out=[]
        
        for i in info["file_loc"]:
            k=i.split("\\")
            
            k1="music//"+k[len(k)-1]
            if out==[]:
                out=[k1]
            else:
                out.append(k1)
        print(out)
        count=0
        for i in info["name"]:
            sql = "UPDATE music SET file_loc = %s WHERE name = %s"
            val = (out[count], i)
            await db.insert(db.conn,sql,val)
            count=count+1
    async def cog_check(self, ctx):
        return await db.perms_check(db,ctx)
def setup(client):
    client.add_cog(music(client))


class musicQueue:
    """description of class"""
    def __init__(self,song):

        self.song= song.lower()
        self.source = None
    async def _init(self):
        self.source= await self.get_source()

    async def get_source(self):
        
        sql = ("SELECT file_loc FROM music where name = '"+self.song+"'")
        print(sql)
        out= await db.get(db.conn, sql)
        filepath=out["file_loc"][0]
        print(filepath)
        FFMPEG_OPTIONS = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
         
        return discord.FFmpegOpusAudio(filepath)
        
        