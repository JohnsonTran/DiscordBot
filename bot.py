import discord
from discord.ext import commands, tasks
import os

client = commands.Bot(command_prefix= '.')

@client.event
async def on_ready():
    print('Bot is ready')

@client.event
async def ping():
    await ctx.send(f'Ping:  {round(client.latency * 1000)}ms')

@client.event
async def clear(ctx, amount = 2):
    await ctx.channel.purge(limit = amount)
    await ctx.send(f'cleared {amount} messages')
    time.sleep(5)
    await ctx.channel.purge(limit = 1)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run("ENTER KEY HERE")