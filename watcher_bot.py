from telethon import TelegramClient, events
import re
import csv
import os

# Deine Telegram-API-Daten
api_id = 24287123
api_hash = '87744a98e27ee88907cafe32f154e2'

# Sessionname
client = TelegramClient("solwatcher_session", api_id, api_hash)

# Liste mit beobachteten Kanälen (wird dynamisch erweitert)
observed_channels = ['spydefi']
known_handles = set()

# Datei zur Speicherung neuer @-Handles
output_file = "entdeckte_telegram_kanäle.csv"

# Datei initialisieren
if not os.path.exists(output_file):
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Handle", "Nachricht", "Zeitstempel"])

# Funktion zur Erkennung von @Handles
def extract_handles(text):
    return re.findall(r'@[\w\d_]{5,}', text)

@client.on(events.NewMessage(chats=observed_channels))
async def handler(event):
    message = event.message.message
    handles = extract_handles(message)

    new_found = []
    for h in handles:
        if h not in known_handles:
            known_handles.add(h)
            new_found.append(h)
            print(f"Neuer Handle entdeckt: {h}")

            with open(output_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([h, message, event.message.date])

    if new_found:
        print(f"{len(new_found)} neue Kanäle in Nachricht gefunden.")

# Starten
print("Watcher läuft…")
client.start()
client.run_until_disconnected()
