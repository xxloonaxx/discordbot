# Multifunctional Discord Bot

Dieser Bot bietet umfangreiche Moderationsfunktionen, VRChat-Gruppenverwaltung sowie einen Musik-Player auf Basis von Lavalink.

## Features

- **Allgemeine Befehle**: Ping, About, dynamischer Prefix.
- **Moderation**: Kick, Ban, Timeout, Slowmode, Warnungen, Purge, Lockdown und Erinnerungen.
- **VRChat-Integration**: Anbindung an die VRChat-API zur Anzeige und Verwaltung von Gruppen, inklusive Promotion-, Demotion- und Invite-Funktionen.
- **Musik**: Verbindung zu einem Lavalink-Knoten via Wavelink mit Befehlen wie Play, Pause, Resume, Stop, Skip und Leave.
- **Reaktionen & Spaß**: Slash-Commands wie `/pat`, `/hug` oder `/slap`, die passende Bilder von nekos.best senden.
- **NSFW**: Slash-Command `/nsfw` mit verschiedenen Kategorien, der nur in entsprechend markierten Kanälen verfügbar ist.

## Setup

1. Python 3.10+ installieren.
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Konfiguration anlegen. Entweder per Umgebungsvariablen oder über eine `botconfig.json` mit folgendem Schema:
   ```json
   {
     "discord": {
       "token": "BOT_TOKEN",
       "guild_ids": [1234567890],
       "default_prefix": "!"
     },
     "vrchat": {
       "username": "VRCHAT_USERNAME",
       "password": "VRCHAT_PASSWORD",
       "two_factor_code": "OPTIONAL_2FA"
     },
     "lavalink": {
       "host": "localhost",
       "port": 2333,
       "password": "youshallnotpass",
       "https": false
     }
   }
   ```
4. Lavalink-Server starten (siehe [Lavalink](https://github.com/freyacodes/Lavalink)).
5. Bot starten:
   ```bash
   python -m main
   ```

## Hinweise

- Die VRChat-API erfordert gültige Anmeldedaten. Für produktive Nutzung sollte ein Applikations-spezifischer Account genutzt werden.
- Musikfunktionen setzen funktionierendes FFMPEG sowie einen Lavalink-Knoten voraus.
- Die Moderationsbefehle erfordern entsprechende Discord-Berechtigungen.

Viel Spaß beim Automatisieren deiner Community!
