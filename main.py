# main.py — Bot sécurisé pour Railway/Replit (Keep-alive + /teste 30s + notifications quotidiennes)
from flask import Flask
import threading
import os
import random
import asyncio
from datetime import datetime, date
import discord
from discord.ext import tasks
from discord import app_commands

# ----- CONFIG via VARIABLES D'ENVIRONNEMENT -----
TOKEN = os.getenv("TOKEN")  # Discord Bot Token
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1446940514879275131"))
NOTIF_HOUR = int(os.getenv("NOTIF_HOUR", "10"))  # Heure française
NOTIF_MINUTE = int(os.getenv("NOTIF_MINUTE", "5"))

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
last_sent_date = None  # date à laquelle la notification a été envoyée
test_task = None
stop_test = False

def is_weekday():
    """Vérifie si c'est un jour de semaine (UTC+1 pour France)"""
    now_utc = datetime.utcnow()
    return now_utc.weekday() < 5

# ----- NOTIFICATIONS QUOTIDIENNES -----
@tasks.loop(seconds=60)
async def send_motivation():
    """Notification quotidienne selon NOTIF_HOUR / NOTIF_MINUTE (heure française)"""
    global last_sent_date

    if not is_weekday():
        return

    now_utc = datetime.utcnow()
    now_hour = (now_utc.hour + 1) % 24  # UTC+1
    now_minute = now_utc.minute
    today = date.today()

    # Debug
    print(f"[DEBUG] UTC+1 actuel : {now_hour:02d}:{now_minute:02d}, last_sent_date={last_sent_date}")

    # Envoie uniquement si l'heure correspond et pas déjà envoyé aujourd'hui
    if (now_hour == NOTIF_HOUR and now_minute == NOTIF_MINUTE) and (last_sent_date != today):
        channel = await bot.fetch_channel(CHANNEL_ID)
        if channel:
            phrase = random.choice(phrases)
            await channel.send(f"[DAILY] {phrase}")
            print(f"[INFO] Message envoyé à {now_hour:02d}:{now_minute:02d}")
        last_sent_date = today

# ----- TASK TEST RAPIDE (30s) -----
async def send_test_phrases():
    global stop_test
    channel = await bot.fetch_channel(CHANNEL_ID)
    while not stop_test:
        phrase = random.choice(phrases)
        await channel.send(f"[TEST 30s] {phrase}")
        await asyncio.sleep(30)

# ----- SLASH COMMANDS -----
@tree.command(name="stop", description="Arrête les notifications pour aujourd'hui")
async def stop_command(interaction: discord.Interaction):
    global last_sent_date
    last_sent_date = date.today()
    await interaction.response.send_message("Notifications arrêtées pour aujourd'hui.", ephemeral=True)

@tree.command(name="start", description="Relance les notifications si elles étaient stoppées")
async def start_command(interaction: discord.Interaction):
    global last_sent_date
    last_sent_date = None
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
    # Test immédiat pour vérifier permissions (NE PAS modifier last_sent_date)
    channel = await bot.fetch_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot ready et permissions OK !")
    send_motivation.start()

# ----- LANCEMENT -----
if not TOKEN:
    print("ERROR: TOKEN non défini dans les variables d'environnement.")
else:
    bot.run(TOKEN)
