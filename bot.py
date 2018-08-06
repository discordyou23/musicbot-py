import discord
from discord.ext import commands
from dsicord.ext.commands import Bot
import asyncio

bot=commands.Bot(command_prefix="$")


@bot.event
async def on_redy():
  print(bot.user.name)


@bot.command(pass_context=True)
async def yt(ctx, url):
  url ='https://www.youtube.com/watch?v=EP625xQIGzs'
  author = ctx.message.author
  voice_channel = author.voice_channel
  vc = await bot.join_voice_channel(voice_channel)

  player = await vc.create_ytdl_player(url)
  player.start()
    
bot.run('MzE3MDkyNzg4Mzc2NDM2NzM2.DbuGZw.GUJSPrTXzfdPrj-cQYT689DL2Rs')
