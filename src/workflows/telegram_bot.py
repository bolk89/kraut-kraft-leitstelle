"""Kraut & Kraft KI-Leitstelle – Telegram-Bot-Workflow.

Pollt eingehende Telegram-Nachrichten, erzeugt mit der Mistral API
deutschsprachige Kurzvideo-Produktionspakete und antwortet im Chat.
"""

import os

import httpx
import mistralai.workflows as workflows
from pydantic import BaseModel

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
MODEL = os.environ.get("KRAUT_MODEL", "mistral-small-latest")
# Kommagetrennte Chat-IDs; leer = alle privaten Chats zulassen
ALLOWED = {x.strip() for x in os.environ.get("KRAUT_ALLOWED_CHAT_IDS", "").split(",") if x.strip()}

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

SYSTEM_PROMPT = ```Du bist die KI-Leitstelle von Kraut & Kraft.

Deine Aufgabe: Erstelle auf Grundlage der Nutzeranfrage fertige deutschsprachige
Inhalte für TikTok, Instagram Reels und YouTube Shorts (9:16).

Erstelle bei einer Videoanfrage:
1. Thema und starken Einstieg (Hook)
2. Vollständiges Sprecher-Skript
3. Szenenplan mit einzelnen Bild- und Videoprompts
4. Deutsche Untertitel, passend zum gesprochenen Text
5. Passende Musik- und Soundhinweise
6. Titel und Covertext
7. Social-Media-Caption mit maximal 600 Zeichen
8. Hashtags
9. Konkrete Schnittanweisungen

STIL: Ruhig, natürlich, professionell, verständlich, visuell hochwertig.
Format 9:16. Texte gut lesbar und innerhalb der sicheren Bildbereiche.

PFLANZENREGELN: Nur sichere, überprüfbare Fakten. Keine Heilversprechen.
Traditionelle Anwendungen entsprechend kennzeichnen. Verwechslungsgefahren
und Giftpflanzen beachten. Unsicheres mit [PRÜFEN] markieren. Bei
Gesundheitsthemen notwendige medizinische Warnhinweise ergänzen.

Antworte strukturiert in Markdown, direkt weiterverarbeitbar.
Bei kurzen Befehlen oder Fragen (z. B. "TEST", "/start") antworte kurz und freundlich.

WICHTIG: Erzeuge keine Behauptung, dass ein Video veröffentlicht oder
geschnitten wurde, wenn das nicht tatsächlich geschehen ist.```


class PollInput(BaseModel):
    """Input für einen Polling-Lauf. Leer, wenn per Schedule getriggert."""


class PollResult(BaseModel):
    processed: int = 0
    errors: int = 0


def _tg(method: str, payload: dict) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{API_BASE}/{method}", json=payload)
        r.raise_for_status()
        return r.json()


async def _generate(user_text: str) -> str:
    from mistralai import Mistral

    client = Mistral()  # nutzt injizierte Credentials im Managed Deployment
    resp = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    return resp.choices[0].message.content or ""


def _send(chat_id: int, text: str) -> None:
    # Telegram-Limit: 4096 Zeichen pro Nachricht
    for i in range(0, len(text), 4000):
        _tg("sendMessage", {
            "chat_id": chat_id,
            "text": text[i:i + 4000],
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        })


@workflows.activity()
async def poll_telegram() -> PollResult:
    """Verarbeitet alle neuen Nachrichten seit der letzten Bestätigung."""
    result = PollResult()

    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN ist nicht gesetzt")

    updates = _tg("getUpdates", {"timeout": 0, "allowed_updates": ["message"]})
    items = updates.get("result", [])
    if not items:
        return result

    last_update_id = 0
    for item in items:
        last_update_id = max(last_update_id, item["update_id"])
        msg = item.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        user_text = (msg.get("text") or "").strip()

        if not chat_id or not user_text:
            continue
        if ALLOWED and str(chat_id) not in ALLOWED:
            continue  # fremde Chats ignorieren

        try:
            answer = await _generate(user_text)
            _send(chat_id, answer)
            result.processed += 1
        except Exception:  # noqa: BLE001
            try:
                _send(chat_id, "⚠️ Entschuldigung, bei der Verarbeitung ist ein Fehler aufgetreten. Bitte später erneut versuchen.")
            except Exception:
                pass
            result.errors += 1

    # Bestätige alle verarbeiteten Updates, damit der nächste Lauf nur Neues sieht
    _tg("getUpdates", {"offset": last_update_id + 1, "timeout": 0, "allowed_updates": ["message"]})
    return result


@workflows.workflow.define(
    name="kraut-kraft-telegram-poll",
    workflow_display_name="Kraut & Kraft Telegram-Poll",
    workflow_description="Pollt Telegram-Updates, erzeugt mit Mistral KI Inhalte und antwortet im Chat.",
)
class TelegramPollWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: PollInput) -> PollResult:
        return await poll_telegram()
