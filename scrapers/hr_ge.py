"""
hr.ge + doctor.ge — POST API.
"""
import time

from http_utils import build_session          # ← ახალი
from logging_utils import get_logger          # ← ახალი
from models import Job
from config import USER_AGENT, REQUEST_DELAY

log = get_logger(__name__)                    # ← ახალი

TENANTS = {
    "hr.ge":     "https://api.p.hr.ge/public-portal/tenant/1/api/v3",
}
ENDPOINT = "/announcement-search"

# Session ერთხელ იქმნება და მთელი მოდულის სიცოცხლის განმავლობაში გამოიყენება
_session = build_session()                    # ← ახალი


def _headers(domain: str) -> dict:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ka-GE,ka;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": f"https://www.{domain}",
        "Referer": f"https://www.{domain}/",
    }


def _fetch(domain: str, base: str, term: str):
    url = f"{base}{ENDPOINT}"
    payload = {
        "Query": term,
        "CategoryIds": [],
        "WorkExperience": {"from": None, "to": None},
        "Start": 0,
        "Limit": 100,
    }
    try:
        r = _session.post(url, json=payload, headers=_headers(domain), timeout=20)  # ← session
        if r.status_code == 200:
            return r.json()
        log.warning("%s '%s': HTTP %s", domain, term, r.status_code)                # ← log
    except Exception as e:
        log.warning("%s '%s': %s", domain, term, e)                                 # ← log
    return None


def _parse(data, domain: str) -> list:
    jobs = []
    if not isinstance(data, dict) or not data.get("success"):
        return jobs

    items = data.get("data", {}).get("announcements", {}).get("items", [])
    for item in items:
        try:
            ann_id = item.get("announcementId")
            title = (item.get("title") or "").strip()
            if not ann_id or not title:
                continue

            url = f"https://www.{domain}/announcement/{ann_id}"
            locations = item.get("locations") or []
            loc_str = ", ".join(locations) if isinstance(locations, list) else str(locations)

            jobs.append(Job(
                source=domain,
                title=title,
                url=url,
                company=(item.get("customerName") or "").strip(),
                location=loc_str or "საქართველო",
                posted=str(item.get("publishDate") or ""),
                deadline=str(item.get("deadlineDate") or ""),
                salary=str(item.get("salary") or ""),
                remote=bool(item.get("isWorkFromHome", False)),
            ))
        except Exception as e:
            log.warning("parse: %s", e)                                              # ← log
    return jobs


def scrape(search_terms=None, progress_callback=None):
    search_terms = search_terms or ["React Developer"]
    all_jobs = []
    total = len(search_terms) * len(TENANTS)
    counter = 0

    for domain, base in TENANTS.items():
        for term in search_terms:
            counter += 1
            if progress_callback:
                progress_callback(counter, total, f"{domain}: '{term}'")

            data = _fetch(domain, base, term)
            if data:
                parsed = _parse(data, domain)
                log.info("%s '%s': %s ვაკანსია", domain, term, len(parsed))          # ← log
                all_jobs.extend(parsed)
            time.sleep(REQUEST_DELAY)

    return all_jobs