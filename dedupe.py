"""ვაკანსიების დედუპლიკაცია — URL და cross-site (title + company)."""
import re
from models import Job

# წყაროს პრიორიტეტი — უფრო სანდო წყარო პირველი
SOURCE_PRIORITY = {
    "hr.ge": 0,
    "doctor.ge": 0,
    "jobs.ge": 1,
    "jobs.ss.ge": 2,
}
_DEFAULT_PRIORITY = 99


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def dedupe(jobs: list[Job], cross_site: bool = True) -> list[Job]:
    """URL-ით და (სურვილისამებრ) title+company-ით დედუპლიკაცია."""
    ordered = sorted(jobs, key=lambda j: SOURCE_PRIORITY.get(j.source, _DEFAULT_PRIORITY))
    seen_urls: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    unique: list[Job] = []

    for j in ordered:
        if not j.url or len(j.url) <= 5 or j.url in seen_urls:
            continue
        seen_urls.add(j.url)

        if cross_site:
            key = (_norm(j.title), _norm(j.company))
            if key[0] and key[1]:
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)

        unique.append(j)

    return unique
