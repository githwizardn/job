"""Telegram შეტყობინებები — უფასო."""
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logging_utils import get_logger
from models import Job

log = get_logger(__name__)

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG = 3500


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram არ არის კონფიგურირებული — გამოტოვებული")
        return False

    try:
        r = requests.post(
            API.format(token=TELEGRAM_BOT_TOKEN),
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text[:MAX_MSG],
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if r.status_code != 200:
            log.warning("Telegram HTTP %s: %s", r.status_code, r.text[:200])
            return False
        log.info("Telegram: გაიგზავნა (%s სიმბოლო)", len(text))
        return True
    except Exception as e:
        log.warning("telegram: %s", e)
        return False


def _esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_digest(jobs: list[Job], search_terms: list[str]) -> str:
    if not jobs:
        return ""

    header = (
        f"🎯 <b>JobRadar</b> — {len(jobs)} ახალი ვაკანსია\n"
        f"<i>ტერმინები: {', '.join(search_terms)}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    by_source: dict[str, list[Job]] = {}
    for j in jobs:
        by_source.setdefault(j.source, []).append(j)

    parts = [header]
    for src, items in sorted(by_source.items()):
        parts.append(f"\n<b>📡 {_esc(src)}</b> ({len(items)})\n")
        for j in items[:8]:
            line = f'• <a href="{j.url}">{_esc(j.title)}</a>'
            if j.company:
                line += f" — {_esc(j.company)}"
            parts.append(line + "\n")
        if len(items) > 8:
            parts.append(f"<i>… და {len(items) - 8} სხვა</i>\n")

    return "".join(parts)