import time

from bs4 import BeautifulSoup

from config import REQUEST_DELAY
from http_utils import build_session
from logging_utils import get_logger
from models import Job

log = get_logger(__name__)

CATEGORY = 6  # IT / პროგრამირება
BASE_URL = "https://jobs.ge"

# Session მოდულის დონეზე — ერთხელ იქმნება, connection pooling მუშაობს
_session = build_session()


# ცნობილი ლოკაციის სიტყვები
_LOCATION_HINTS = (
    "tbilisi", "batumi", "kutaisi", "rustavi", "gori", "zugdidi",
    "telavi", "poti", "ozurgeti", "kvemo kartli", "shida kartli",
    "თბილისი", "ბათუმი", "ქუთაისი", "რუსთავი", "გორი", "ზუგდიდი",
    "თელავი", "ფოთი", "ოზურგეთი", "საქართველო",
    "remote", "რემოუტ", "hybrid", "ჰიბრიდ",   # ← "dist" წაშლილია
)


def _parse_location(loc_text: str) -> str:
    """ამოიღებს ლოკაციას 'title - location' ფორმატიდან.
    თუ ლოკაცია ცნობილი არ არის → ცარიელი სტრინგი."""
    if " - " not in loc_text:
        return ""
    candidate = loc_text.split(" - ", 1)[1].strip()
    if any(h in candidate.lower() for h in _LOCATION_HINTS):
        return candidate
    return ""


def scrape(search_terms=None, progress_callback=None):
    """
    jobs.ge — HTML parsing.

    URL ფორმატი: https://jobs.ge/en/?page=1&q=TERM&cid=6&lid=
    - /en/ — ინგლისური ვერსია (სუფთა HTML)
    - q=TERM უნდა იყოს UPPERCASE
    - lid= ცარიელი → ყველა ლოკაცია
    """
    search_terms = search_terms or ["React Developer"]
    all_jobs = []
    total = len(search_terms)

    for i, term in enumerate(search_terms):
        if progress_callback:
            progress_callback(i, total, f"jobs.ge: '{term}'")

        url = f"{BASE_URL}/en/?page=1&q={term.upper()}&cid={CATEGORY}&lid="

        try:
            r = _session.get(url, timeout=15)
            r.encoding = "utf-8"

            if r.status_code != 200:
                log.warning("jobs.ge '%s': HTTP %s", term, r.status_code)
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", id="job_list_table")

            if not table:
                log.warning("jobs.ge '%s': table ვერ მოიძებნა", term)
                continue

            rows = table.find_all("tr")[1:]
            count = 0

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                a_tag = cols[1].find("a", class_="vip") or cols[1].find("a")
                if not a_tag or not a_tag.get("href"):
                    continue

                href = a_tag["href"]
                full_url = href if href.startswith("http") else f"{BASE_URL}{href}"

                # ლოკაცია სათაურიდან
                loc_text = cols[1].get_text(" ", strip=True)
                location = _parse_location(loc_text)

                # remote შემოწმება
                loc_lower = loc_text.lower()
                is_remote = (
                    "დისტანციური" in loc_lower
                    or "დისტანციით" in loc_lower
                    or "remote" in loc_lower
                )

                all_jobs.append(Job(
                    source="jobs.ge",
                    title=a_tag.get_text(strip=True),
                    url=full_url,
                    company=cols[3].get_text(strip=True) if len(cols) > 3 else "",
                    location=location,   # ← "" თუ უცნობია; filters.py გადაწყვეტს
                    posted=cols[4].get_text(strip=True) if len(cols) > 4 else "",
                    deadline=cols[5].get_text(strip=True) if len(cols) > 5 else "",
                    remote=is_remote,
                ))
                count += 1

            log.info("jobs.ge '%s': %s ვაკანსია", term, count)
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            log.warning("jobs.ge '%s': %s", term, e)

    return all_jobs