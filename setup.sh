#!/usr/bin/env bash
# Kraut & Kraft KI-Leitstelle – Setup für Synology / Linux
# Aufruf im Projektordner:  bash setup.sh
set -euo pipefail

echo "=== Kraut & Kraft KI-Leitstelle – Setup ==="

# Docker prüfen (Synology: Container Manager muss installiert sein)
if ! command -v docker >/dev/null 2>&1; then
  echo "FEHLER: Docker nicht gefunden. Bitte Container Manager im Paket-Zentrum installieren."
  exit 1
fi

if ! (docker info >/dev/null 2>&1); then
  echo "Docker erfordert Root-Rechte – bitte Passwort eingeben, falls gefragt."
  SUDO="sudo"
else
  SUDO=""
fi

if [ -f .env ]; then
  echo "Bestehende .env gefunden – verwende sie. (Löschen mit: rm .env für Neuanlage)"
else
  echo ""
  echo "Bitte die beiden Tokens bereithalten:"
  echo "  1) Mistral-API-Key:  https://console.mistral.ai/api-keys"
  echo "  2) Telegram-Bot-Token (von @BotFather)"
  echo ""
  read -rp "Mistral-API-Key: " MISTRAL_KEY
  read -rp "Telegram-Bot-Token: " TG_TOKEN
  read -rp "Deine Telegram-Chat-ID [leer lassen = alle Chats erlauben]: " CHAT_IDS

  cat > .env <<EOF
MISTRAL_API_KEY=\${MISTRAL_KEY}
TELEGRAM_BOT_TOKEN=\${TG_TOKEN}
KRAUT_ALLOWED_CHAT_IDS=\${CHAT_IDS}
EOF
  chmod 600 .env
  echo ".env angelegt."
fi

echo ""
echo "Baue und starte den Container ..."
\${SUDO} docker compose up -d --build

echo ""
echo "Status:"
\${SUDO} docker compose ps

echo ""
echo "Warte 10 Sekunden auf die ersten Logs ..."
sleep 10
echo ""
echo "=== Letzte Logs (Strg+C zum Beenden der Loganzeige) ==="
\${SUDO} docker compose logs --tail 30 -f
