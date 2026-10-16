"""ვაკანსიის ქულა — უკეთესი პირველ ადგილზე."""
from datetime import datetime, timedelta, timezone

from config import CONTRACTOR_SIGNALS
from models import Job

_REMOTE_WORDS = ("remote", "რემოუტ", "დისტანციურ", "anywhere", "worldwide")
_GEORGIAN_SOURCES = {"hr.ge", "jobs.ge", "jobs.ss.ge", "doctor.ge"}


def score(job: Job, search_terms: list[str]) -> int:
    s = 0
    title = (job.title or "").lower()
    loc = (job.location or "").lower()
    desc = (job.description or "").lower()

    # 1. ტერმინი სათაურში — ყველაზე მთავარი
    for term in search_terms:
        if term.lower() in title:
            s += 30
            break

    # 2. remote / ლოკაცია
    if any(w in title for w in _REMOTE_WORDS):
        s += 15
    if "tbilisi" in loc or "თბილისი" in loc or "batumi" in loc or "ბათუმი" in loc:
        s += 15
    elif "remote" in loc or "worldwide" in loc or "anywhere" in loc:
        s += 10

    # 3. ხელფასი მითითებულია
    if job.salary and job.salary.strip():
        s += 8

    # 4. კონტრაქტი — ნაკლები ბიუროკრატია
    if any(sig in desc[:3000] for sig in CONTRACTOR_SIGNALS):
        s += 5

    # 5. სიახლე
    if _is_recent(job.posted, hours=72):
        s += 12
    elif _is_recent(job.posted, hours=24 * 14):
        s += 5

    # 6. ქართული წყარო — უფრო ადვილი კონტაქტი
    if job.source in _GEORGIAN_SOURCES:
        s += 6

    return s


def _is_recent(posted: str, hours: int) -> bool:
    if not posted:
        return False
    try:
        s = posted.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return False

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - dt < timedelta(hours=hours)