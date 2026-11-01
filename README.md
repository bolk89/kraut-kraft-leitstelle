# Kraut & Kraft – KI-Leitstelle

Telegram-Bot als Mistral Workflow: Pollt eingehende Nachrichten an
@KrautKraftLeitstelleBot, erzeugt mit der Mistral API komplette
Kurzvideo-Produktionspakete (TikTok / Reels / Shorts, 9:16) und antwortet
direkt im Chat.

## Aufbau

- `src/workflows/telegram_bot.py` – Workflow `kraut-kraft-telegram-poll`
- `src/entrypoints/worker.py` – Worker-Einstiegspunkt
- `Dockerfile` – Build für Managed Deployments

## Erforderliche Umgebungsvariablen (Workspace-Secrets)

- `TELEGRAM_BOT_TOKEN` – Bot-Token von @BotFather
- Optional: `KRAUT_ALLOWED_CHAT_IDS` – kommagetrennte Chat-IDs (leer = alle privaten Chats)
- Optional: `KRAUT_MODEL` – Standard: `mistral-small-latest`

## Sicherheit

- Der Bot antwortet nur in privaten Chats; mit `KRAUT_ALLOWED_CHAT_IDS` lässt
  sich der Zugriff auf bestimmte Chat-IDs beschränken.
- Der Token liegt nie im Repository, sondern in den Workspace-Secrets.
