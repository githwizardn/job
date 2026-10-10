"""
Remotive.com — უფასო public API, remote ვაკანსიები.
https://remotive.com/api/remote-jobs
"""
import requests
from models import Job
from config import USER_AGENT


API_URL = "https://remotive.com/api/remote-jobs"


def scrape(search_terms=None, progress_callback=None):
    search_terms = search_terms or ["junior"]
    all_jobs = []

    headers = {"User-Agent": USER_AGENT}
    seen_urls = set()

    total = len(search_terms)
    for i, term in enumerate(search_terms):
        if progress_callback:
            progress_callback(i, total, f"remotive: '{term}'")

        try:
            r = requests.get(
                API_URL,
                params={"search": term, "limit": 100},
                headers=headers,
                timeout=20,
            )
            if r.status_code != 200:
                print(f"     ⚠ remotive '{term}': HTTP {r.status_code}")
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
                    import re
                    desc = item.get("description") or ""
                    desc = re.sub(r"<[^>]+>", " ", desc)[:2000]

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
                    print(f"     ⚠ remotive parse: {e}")

            print(f"     ✓ remotive '{term}': {count}")
        except Exception as e:
            print(f"     ✗ remotive '{term}': {e}")

    return all_jobs