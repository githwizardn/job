"""
Remotive.com — უფასო public API, remote ვაკანსიები.
https://remotive.com/api/remote-jobs
"""
import re
from typing import Optional

from http_utils import build_session
from logging_utils import get_logger
from models import Job

log = get_logger(__name__)

API_URL = "https://remotive.com/api/remote-jobs"
_TAG_RE = re.compile(r"<[^>]+>")


def scrape(search_terms: Optional[list[str]] = None,
           progress_callback=None) -> list[Job]:
    search_terms = search_terms or ["junior"]
    all_jobs: list[Job] = []
    session = build_session()
    seen_urls: set[str] = set()

    total = len(search_terms)
    for i, term in enumerate(search_terms):
        if progress_callback:
            progress_callback(i, total, f"remotive: '{term}'")

        try:
            r = session.get(
                API_URL,
                params={"search": term, "limit": 100},
                timeout=20,
            )
            if r.status_code != 200:
                log.warning("remotive '%s': HTTP %s", term, r.status_code)
                continue

            data = r.json()
            items = data.get("jobs", []) if isinstance(data, dict) else []
            count = 0

            for item in items:
                try:
                    url = (item.get("url") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not url or not title or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # candidate_required_location — "Worldwide", "Europe", "USA Only" etc.
                    loc = (item.get("candidate_required_location") or "").strip()

                    # description არის HTML — ჩამოვაშოროთ tag-ები
                    desc = _TAG_RE.sub(" ", item.get("description") or "")[:2000]

                    all_jobs.append(Job(
                        source="remotive",
                        title=title,
                        url=url,
                        company=(item.get("company_name") or "").strip(),
                        location=loc or "Remote",
                        posted=str(item.get("publication_date") or ""),
                        salary=str(item.get("salary") or ""),
                        remote=True,
                        description=desc,
                    ))
                    count += 1
                except Exception as e:
                    log.warning("remotive parse: %s", e)

            log.info("remotive '%s': %s", term, count)
        except Exception as e:
            log.exception("remotive '%s': %s", term, e)

    return all_jobs