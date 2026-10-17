"""Telegram შეტყობინებები — უფასო."""
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logging_utils import get_logger
from models import Job

log = get_logger(__name__)

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG = 3800  # Telegram-ის ლიმიტი 4096


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram არ არის კონფიგურირებული — გამოტოვებული")
        return False

    try:
        # უსაფრთხო ჩამოჭრა (რომ HTML ტეგი არ გავწყვიტოთ)
        safe_text = text[:MAX_MSG]
        if len(text) > MAX_MSG:
            # თუ ბოლო "<"-ს და ">"-ს შორის ვართ, მაშინ ტეგი შუაშია გაჭრილი
            if safe_text.rfind("<") > safe_text.rfind(">"):
                safe_text = safe_text[:safe_text.rfind("<")] + "...\n\n<i>დანარჩენი ვაკანსიები ნახე History-ში</i>"
            else:
                safe_text += "\n\n<i>დანარჩენი ვაკანსიები ნახე History-ში</i>"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": safe_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        
        r = requests.post(API.format(token=TELEGRAM_BOT_TOKEN), json=payload, timeout=15)
        
        # თუ HTML-ის გამო მაინც 500/400 შეცდომაა, ვცადოთ HTML-ის გარეშე
        if r.status_code != 200:
            log.warning("HTML parse error. Retrying without HTML...")
            payload.pop("parse_mode", None)
            r = requests.post(API.format(token=TELEGRAM_BOT_TOKEN), json=payload, timeout=15)

        if r.status_code != 200:
            log.warning("Telegram HTTP %s: %s", r.status_code, r.text[:200])
            return False
            
        log.info("Telegram: გაიგზავნა (%s სიმბოლო)", len(safe_text))
        return True
    except Exception as e:
        log.warning("telegram: %s", e)
        return False


def _esc(s: str) -> str:
    """HTML escaping — Telegram parse_mode=HTML-ისთვის."""
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_digest(jobs: list[Job], search_terms: list[str]) -> str:
    """ერთი დიდი შეტყობინება ყველა ახალი ვაკანსიით."""
    if not jobs:
        return ""

    header = (
        f"🎯 <b>JobRadar</b> — {len(jobs)} ახალი ვაკანსია\n"
        f"<i>ტერმინები: {', '.join(search_terms)}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    # ჯგუფებად წყაროების მიხედვით
    by_source: dict[str, list[Job]] = {}
    for j in jobs:
        by_source.setdefault(j.source, []).append(j)

    parts = [header]
    for src, items in sorted(by_source.items()):
        parts.append(f"\n<b>📡 {_esc(src)}</b> ({len(items)})\n")
        # ვაჩვენოთ მაქსიმუმ 5 ვაკანსია თითო წყაროზე (რომ ტექსტი არ გაიწელოს)
        for j in items[:5]:
            line = f'• <a href="{j.url}">{_esc(j.title)}</a>'
            if j.company:
                line += f" — {_esc(j.company)}"
            parts.append(line + "\n")
        if len(items) > 5:
            parts.append(f"<i>… და {len(items) - 5} სხვა</i>\n")

    return "".join(parts)