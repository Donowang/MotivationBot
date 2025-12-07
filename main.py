# main.py — Bot sécurisé pour Railway/Replit (Keep-alive + /teste 30s + notifications quotidiennes)

from flask import Flask
import threading
import os
import random
import asyncio
from datetime import datetime
import discord
from discord.ext import tasks
from discord import app_commands

# ----- CONFIG via VARIABLES D'ENVIRONNEMENT -----
TOKEN = os.getenv("TOKEN")  # configure dans Railway: ton token Discord
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1446940514879275131"))
NOTIF_HOUR = int(os.getenv("NOTIF_HOUR", "8"))
NOTIF_MINUTE = int(os.getenv("NOTIF_MINUTE", "42"))

# ----- KEEP-ALIVE (Flask) -----
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask).start()

# ----- DISCORD BOT -----
phrases = [
    "Tu crois que tu vas te muscler comme ça ?!",
    "Regarde comment il te regarde...",
    "Tu veux rester moche toute ta vie ?",
    "Bouge-toi !",
    "Courage, ça vaut le coup !",
    "Allez, donne tout !",
    "Rien ne tombe du ciel, faut bosser !",
    "Chaque effort compte !",
]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ----- VARIABLES -----
stop_today = False
test_task = None
stop_test = False

def is_weekday():
    return datetime.now().weekday() < 5  # 0=lundi

# ----- NOTIFICATIONS QUOTIDIENNES -----
@tasks.loop(seconds=60)
async def send_motivation():
    global stop_today
    if stop_today or not is_weekday():
        return

    now = datetime.now()
    if now.hour == NOTIF_HOUR and now.minute == NOTIF_MINUTE:
        channel = await bot.fetch_channel(CHANNEL_ID)
        if channel:
            phrase = random.choice(phrases)
            await channel.send(phrase)
        stop_today = True

# ----- TASK POUR /TESTE (30s) -----
async def send_test_phrases():
    global stop_test
    channel = await bot.fetch_channel(CHANNEL_ID)
    while not stop_test:
        phrase = random.choice(phrases)
        await channel.send(f"[TEST] {phrase}")
        await asyncio.sleep(30)

# ----- SLASH COMMANDS -----
@tree.command(name="stop", description="Arrête les notifications pour aujourd'hui")
async def stop_command(interaction: discord.Interaction):
    global stop_today
    stop_today = True
    await interaction.response.send_message("Notifications arrêtées pour aujourd'hui.", ephemeral=True)

@tree.command(name="start", description="Relance les notifications si elles étaient stoppées")
async def start_command(interaction: discord.Interaction):
    global stop_today
    stop_today = False
    await interaction.response.send_message("Notifications relancées !", ephemeral=True)

@tree.command(name="teste", description="Teste l'envoi toutes les 30 sec d'une phrase")
async def teste_command(interaction: discord.Interaction):
    global test_task, stop_test
    if test_task and not test_task.done():
        await interaction.response.send_message("Le test est déjà en cours !", ephemeral=True)
        return
    stop_test = False
    await interaction.response.send_message("Test démarré : phrases envoyées toutes les 30 sec.", ephemeral=True)
    test_task = bot.loop.create_task(send_test_phrases())

@tree.command(name="stopteste", description="Arrête le test des phrases toutes les 30 sec")
async def stopteste_command(interaction: discord.Interaction):
    global stop_test
    stop_test = True
    await interaction.response.send_message("Test arrêté.", ephemeral=True)

# ----- BOT READY -----
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    await tree.sync()
    send_motivation.start()

# ----- LANCEMENT -----
if not TOKEN:
    print("ERROR: TOKEN non défini dans les variables d'environnement.")
else:
    bot.run(TOKEN)
