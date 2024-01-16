from discord.ext import commands
from db import db

class perms(commands.Cog):
    """description of class"""
    
    def __init__(self, client):
        self.client = client

    @commands.command(help="Toggle whitelist mode for users.")
    async def white_user(self, ctx):
        guild_id = str(ctx.guild.id)
        current_mode = db.perms_cache[guild_id]["isWhite_user"]
        new_mode = not current_mode

        db.perms_cache[guild_id]["isWhite_user"] = new_mode
        sql = f"UPDATE discord_servers SET isWhite_user= {int(new_mode)} WHERE discord_server = {guild_id}"
        await db.insert(sql)

        await ctx.send(f"Whitelist mode for users is now {'enabled' if new_mode else 'disabled'}.")

    @commands.command(help="Toggle whitelist mode for channels.")
    async def white_ch(self, ctx):
        guild_id = str(ctx.guild.id)
        current_mode = db.perms_cache[guild_id]["isWhite_ch"]
        new_mode = not current_mode

        db.perms_cache[guild_id]["isWhite_ch"] = new_mode
        sql = f"UPDATE discord_servers SET isWhite_ch= {int(new_mode)} WHERE discord_server = {guild_id}"
        await db.insert(sql)

        await ctx.send(f"Whitelist mode for channels is now {'enabled' if new_mode else 'disabled'}.")

    @commands.command(help="Blacklist or whitelist a user or channel.")
    async def toggle_list(self, ctx, input_id, list_type="black"):
        # Extracting the ID from the input
        target_id = input_id[2:-1]

        # Check if the ID is for a channel or user
        is_channel = any(str(channel.id) == target_id for channel in ctx.guild.channels)
        is_user = any(str(user.id) == target_id for user in ctx.guild.members)

        if not (is_channel or is_user):
            await ctx.send("Invalid ID provided.")
            return

        list_key = f"{list_type}_list"
        if target_id in db.perms_cache[ctx.guild.id][list_key]:
            db.perms_cache[ctx.guild.id][list_key].remove(target_id)
            action = "Removed from"
        else:
            db.perms_cache[ctx.guild.id][list_key].append(target_id)
            action = "Added to"

        # Update the database
        if action == "Added to":
            sql = f"INSERT INTO discord_{ctx.guild.id}({list_key}) VALUES({target_id})"
        else:
            sql = f"DELETE FROM discord_{ctx.guild.id} WHERE {list_key} = {target_id}"
        await db.insert(sql)

        await ctx.send(f"{target_id} {action} the {list_type}list.")

    async def cog_check(self, ctx):
        return await db.perms_check(ctx)

def setup(client):
    client.add_cog(perms(client))