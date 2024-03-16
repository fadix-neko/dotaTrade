import os
import discord
from discord.ext import commands
import cfg

client = commands.AutoShardedBot(command_prefix='$', intents=discord.Intents.all(), help_command=None)

@client.event
async def on_application_command_error(ctx, exception):
    if isinstance(exception, discord.errors.CheckFailure):
        await ctx.respond("У Вас недостаточно прав для этого действия!", ephemeral=True)
    elif isinstance(exception, discord.errors.Forbidden):
        await ctx.respond(f"У {client.user.mention} недостаточно прав для выполнения этого действия!", ephemeral=True)
    else:
        raise exception

@client.event
async def on_ready():
    print(f'{client.user} started | WS Ping: {client.latency*1000} ms')
    await client.change_presence(activity=discord.Game(name=cfg.STATUS))

for _ in os.listdir("cogs"):
    if _[:-3] != "__pycach": client.load_extension(f"cogs.{_[:-3]}")

client.run(cfg.TOKEN)
