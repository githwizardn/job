import time
import requests
from bs4 import BeautifulSoup
from models import Job
from config import USER_AGENT, REQUEST_DELAY


CATEGORY = 6  # IT / პროგრამირება
BASE_URL = "https://jobs.ge"


# ცნობილი ლოკაციის სიტყვები — თუ " - " შემდეგ ეს არ არის, "საქართველო"-თი ჩანაცვლდება
_LOCATION_HINTS = (
    "tbilisi", "batumi", "kutaisi", "rustavi", "gori", "zugdidi",
    "telavi", "poti", "ozurgeti", "kvemo kartli", "shida kartli",
    "თბილისი", "ბათუმი", "ქუთაისი", "რუსთავი", "გორი", "ზუგდიდი",
    "თელავი", "ფოთი", "ოზურგეთი", "საქართველო",
    "remote", "რემოუტ", "hybrid", "ჰიბრიდ", "dist",
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
    headers = {"User-Agent": USER_AGENT}
    total = len(search_terms)

    for i, term in enumerate(search_terms):
        if progress_callback:
            progress_callback(i, total, f"jobs.ge: '{term}'")

        url = f"{BASE_URL}/en/?page=1&q={term.upper()}&cid={CATEGORY}&lid="

        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = "utf-8"

            if r.status_code != 200:
                print(f"     ⚠ jobs.ge '{term}': HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", id="job_list_table")

            if not table:
                print(f"     ⚠ jobs.ge '{term}': table ვერ მოიძებნა")
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
                    or "remote" in loc_lower
                    or "dist" in loc_lower
                )

                all_jobs.append(Job(
                    source="jobs.ge",
                    title=a_tag.get_text(strip=True),
                    url=full_url,
                    company=cols[3].get_text(strip=True) if len(cols) > 3 else "",
                    location=location or "საქართველო",
                    posted=cols[4].get_text(strip=True) if len(cols) > 4 else "",
                    deadline=cols[5].get_text(strip=True) if len(cols) > 5 else "",
                    remote=is_remote,
                ))
                count += 1

            print(f"     ✓ jobs.ge '{term}': {count} ვაკანსია")
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"     ✗ jobs.ge '{term}': {e}")

    return all_jobs