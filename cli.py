"""
JobRadar CLI — ავტომატური გაშვებისთვის (cron, GitHub Actions).

გამოყენება:
    python cli.py              # ჩვეულებრივი გაშვება
    python cli.py --no-notify  # Telegram-ის გარეშე (ტესტი)
"""
import argparse
import importlib
import json
import sys
from pathlib import Path

from config import ENABLED_SCRAPERS, MY_TERMS_FILE
from db import connect, stats, upsert
from dedupe import dedupe
from filters import filter_jobs
from logging_utils import get_logger
from notify import format_digest, send_telegram
from scoring import score

log = get_logger("cli")

# წყარო → (მოდული, დამატებითი kwargs)
SCRAPER_REGISTRY = {
    "jobspy":     ("jobspy_scraper", {"results_wanted": 25, "hours_old": 168}),
    "jobs_ge":    ("jobs_ge", {}),
    "hr_ge":      ("hr_ge", {}),
    "jobs_ss_ge": ("jobs_ss_ge", {}),
    "remotive":   ("remotive_scraper", {}),
     "remoteok":         ("remoteok", {}),          # ← ახალი
    "weworkremotely":   ("weworkremotely", {}),  
}


def load_terms() -> list[str]:
    p = Path(MY_TERMS_FILE)
    if not p.exists():
        return []
    try:
        # utf-8-sig ავტომატურად შლის BOM-ს თუ არსებობს
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return [t for t in data if t.strip()]
    except Exception as e:
        log.error("my_terms.json ვერ ჩაიტვირთა: %s", e)
        return []


def run(notify: bool = True) -> int:
    terms = load_terms()
    if not terms:
        log.error("ტერმინები ცარიელია — ჩაწერე %s-ში", MY_TERMS_FILE)
        return 1

    log.info("=" * 60)
    log.info("ვეძებ: %s", ", ".join(terms))
    log.info("=" * 60)

    all_jobs = []
    for name in ENABLED_SCRAPERS:
        mod_name, extra = SCRAPER_REGISTRY.get(name, (None, None))
        if not mod_name:
            continue
        try:
            mod = importlib.import_module(f"scrapers.{mod_name}")
            jobs = mod.scrape(search_terms=terms, **extra)
            log.info("✓ %s: %s ვაკანსია", name, len(jobs))
            all_jobs.extend(jobs)
        except Exception as e:
            log.exception("✗ %s ვერ დასრულდა: %s", name, e)

    if not all_jobs:
        log.warning("ვერაფერი მოიძებნა")
        return 0

    all_jobs = dedupe(all_jobs, cross_site=True)
    log.info("დედუპლიკაციის შემდეგ: %s", len(all_jobs))

    kept, fstats = filter_jobs(all_jobs, terms)
    log.info(
        "ფილტრის შემდეგ: %s (მოიხსნა %s title, %s geo)",
        len(kept),
        fstats["title_removed"],
        fstats["geo_removed"],
    )

    conn = connect()
    try:
        new_jobs = upsert(conn, kept, score_fn=lambda j: score(j, terms))
        st = stats(conn)
    finally:
        conn.close()

    log.info("🆕 ახალი ვაკანსია: %s", len(new_jobs))
    log.info("📊 სულ ბაზაში: %s (24სთ-ში: %s, მიმართული: %s)",
             st["total"], st["last_24h"], st["applied"] or 0)

    if new_jobs:
        new_jobs.sort(key=lambda j: score(j, terms), reverse=True)
        if notify:
            text = format_digest(new_jobs, terms)
            if send_telegram(text):
                log.info("✈️ Telegram: გაგზავნილია")

    log.info("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(description="JobRadar CLI")
    parser.add_argument("--no-notify", action="store_true",
                        help="Telegram-ის გარეშე")
    args = parser.parse_args()

    sys.exit(run(notify=not args.no_notify))


if __name__ == "__main__":
    main()