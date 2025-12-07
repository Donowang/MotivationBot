# main.py — Notifications toutes les 3 minutes pour test + /muscufais + compte à rebours
from flask import Flask
import threading
import os
import random
import asyncio
from datetime import datetime, timedelta
import discord
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
next_notification_time = None
timer_message = None

def is_weekday():
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    return now.weekday() < 5

# ----- NOTIFICATIONS TOUTES LES 3 MINUTES (TEST) -----
async def send_periodic_motivation():
    global stop_notifications, next_notification_time, timer_message
    interval = timedelta(minutes=3)  # TEST : toutes les 3 minutes

    channel = await bot.fetch_channel(CHANNEL_ID)
    if not channel:
        return

    # Initialise le timer
    now = datetime.utcnow() + timedelta(hours=1)
    next_notification_time = now + interval

    # Crée le message timer si nécessaire
    if timer_message is None:
        timer_message = await channel.send("⏳ Prochain rappel dans 03:00")

    while True:
        now = datetime.utcnow() + timedelta(hours=1)

        # Envoie la phrase motivante si le timer est écoulé
        if is_weekday() and not stop_notifications and now >= next_notification_time:
            phrase = random.choice(phrases)
            await channel.send(f"[MOTIVATION] {phrase}")
            print(f"[INFO] Message envoyé à {now}")
            # Relance automatique du timer
            next_notification_time = now + interval

        # Calcul du compte à rebours
        remaining = int((next_notification_time - now).total_seconds())
        if remaining < 0:
            remaining = 0
        minutes, secondes = divmod(remaining, 60)

        # Met à jour le message timer
        if timer_message:
            try:
                await timer_message.edit(content=f"⏳ Prochain rappel dans {minutes:02d}:{secondes:02d}")
            except discord.HTTPException:
                # Si le message a été supprimé, recrée un nouveau message
                timer_message = await channel.send(f"⏳ Prochain rappel dans {minutes:02d}:{secondes:02d}")

        await asyncio.sleep(1)

# ----- SLASH COMMANDS -----
@tree.command(name="muscufais", description="Arrête les notifications pour le reste de la journée")
async def muscufais_command(interaction: discord.Interaction):
    global stop_notifications
    stop_notifications = True
    await interaction.response.send_message("💪 Notifications arrêtées pour aujourd'hui.", ephemeral=True)

@tree.command(name="prochaine", description="Affiche le temps avant la prochaine notification")
async def prochaine_command(interaction: discord.Interaction):
    if next_notification_time is None:
        await interaction.response.send_message("⏱ Calcul du prochain rappel...")
        return
    now = datetime.utcnow() + timedelta(hours=1)
    delta = next_notification_time - now
    minutes, secondes = divmod(int(delta.total_seconds()), 60)
    await interaction.response.send_message(f"⏱ Prochaine notification dans {minutes}m {secondes}s")

# ----- BOT READY -----
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    await tree.sync()
    channel = await bot.fetch_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot ready et permissions OK !")
    # Lance le timer en tâche parallèle
    bot.loop.create_task(send_periodic_motivation())

# ----- LANCEMENT -----
if not TOKEN:
    print("ERROR: TOKEN non défini")
else:
    bot.run(TOKEN)
