import discord
from discord.ext import commands


command_attrs = {'hidden':True}
class Help(commands.MinimalHelpCommand):

    #https://gist.github.com/InterStella0/b78488fb28cadf279dfd3164b9f0cf96 
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help")
        embed.add_field(name="1!help", value="1!help gives a list off all the commands",inline=False)
        embed.add_field(name="1!white", value="1!white #channel/@username ",inline=False)
        embed.add_field(name="1!black", value="1!black #channel/@username ",inline=False)
        embed.add_field(name="1!white_user", value="1!white_user toggles white list for users",inline=False)
        embed.add_field(name="1!white_ch", value="1!white_ch toggles white list for channles",inline=False)
        embed.add_field(name="1!play", value="1!play song or resumes song if left blank",inline=False)
        embed.add_field(name="1!pause", value="1!pause pauses the current song",inline=False)
        embed.add_field(name="1!skip", value="1!skip skipps current song",inline=False)
        embed.add_field(name="1!stop", value="1!stop stops the music",inline=False)
        embed.add_field(name="1!join", value="1!join makes the bot join the chat",inline=False)
        embed.add_field(name="1!disconnect", value="1!disconnect makes bot leave voice channle",inline=False)
        embed.add_field(name="1!list_songs", value="1!list_songs list all songs avable to pick from",inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)