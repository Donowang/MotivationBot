# main.py — Notifications toutes les 2h30 + /muscufais + compte à rebours
from flask import Flask
import threading
import os
import random
import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import tasks
from discord import app_commands

# ----- CONFIG -----
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1446940514879275131"))

# ----- KEEP-ALIVE -----
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
    "Bouge-toi !",
    "Courage, ça vaut le coup !",
    "Allez, donne tout !",
    "Chaque effort compte !",
]

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ----- VARIABLES -----
stop_notifications = False
test_task = None
stop_test = False
next_notification_time = None
timer_message = None

def is_weekday():
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    return now.weekday() < 5

# ----- NOTIFICATIONS TOUTES LES 2H30 AVEC TIMER -----
async def send_periodic_motivation():
    global stop_notifications, next_notification_time, timer_message
    interval = timedelta(hours=2, minutes=30)
    now = datetime.utcnow() + timedelta(hours=1)
    next_notification_time = now + interval

    channel = await bot.fetch_channel(CHANNEL_ID)
    if not channel:
        return

    # Crée le message timer si nécessaire
    if timer_message is None:
        timer_message = await channel.send("⏳ Prochain rappel dans 2h30:00")

    while True:
        now = datetime.utcnow() + timedelta(hours=1)
        if is_weekday() and not stop_notifications:
            if now >= next_notification_time:
                phrase = random.choice(phrases)
                await channel.send(f"[MOTIVATION] {phrase}")
                print(f"[INFO] Message envoyé à {now}")
                next_notification_time = now + interval

        # Met à jour le timer toutes les secondes
        remaining = int((next_notification_time - now).total_seconds())
        if remaining < 0:
            remaining = 0
        heures, reste = divmod(remaining, 3600)
        minutes, secondes = divmod(reste, 60)
        await timer_message.edit(content=f"⏳ Prochain rappel dans {heures:02d}:{minutes:02d}:{secondes:02d}")
        await asyncio.sleep(1)

# ----- TASK TEST RAPIDE (30s) -----
async def send_test_phrases():
    global stop_test
    channel = await bot.fetch_channel(CHANNEL_ID)
    while not stop_test:
        phrase = random.choice(phrases)
        await channel.send(f"[TEST 30s] {phrase}")
        await asyncio.sleep(30)

# ----- SLASH COMMANDS -----
@tree.command(name="muscufais", description="Arrête les notifications pour le reste de la journée")
async def muscufais_command(interaction: discord.Interaction):
    global stop_notifications
    stop_notifications = True
    await interaction.response.send_message("💪 Notifications arrêtées pour aujourd'hui.", ephemeral=True)

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

@tree.command(name="prochaine", description="Affiche le temps avant la prochaine notification")
async def prochaine_command(interaction: discord.Interaction):
    if next_notification_time is None:
        await interaction.response.send_message("⏱ Calcul du prochain rappel...")
        return
    now = datetime.utcnow() + timedelta(hours=1)
    delta = next_notification_time - now
    heures, reste = divmod(int(delta.total_seconds()), 3600)
    minutes, secondes = divmod(reste, 60)
    await interaction.response.send_message(
        f"⏱ Prochaine notification dans {heures}h {minutes}m {secondes}s"
    )

# ----- BOT READY -----
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    await tree.sync()
    channel = await bot.fetch_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot ready et permissions OK !")
    bot.loop.create_task(send_periodic_motivation())

# ----- LANCEMENT -----
if not TOKEN:
    print("ERROR: TOKEN non défini")
else:
    bot.run(TOKEN)
