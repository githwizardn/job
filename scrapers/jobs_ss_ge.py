"""
jobs.ss.ge — Next.js data endpoint + job detail fetch.

მთავარი გაუმჯობესებები:
1. buildId-ის ავტო-refresh 404-ზე + TTL
2. JSON სტრუქტურის recursive ძებნა — key-ების გამოცნობა აღარ გვჭირდება
3. ვაკანსიის დეტალური გვერდის ჩამოტვირთვა → description
   (ამის გარეშე RESTRICTED_KEYWORDS ვერ მუშაობს!)
4. პაგინაცია
5. HTML fallback თუ JSON ვერ მოვიძიეთ
"""
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
from bs4 import BeautifulSoup

from http_utils import build_session
from logging_utils import get_logger
from models import Job
from config import REQUEST_DELAY, DETAIL_WORKERS

log = get_logger(__name__)

BASE_URL = "https://jobs.ss.ge"
LIST_PATH = "/ka/l/vacancies"
_BUILD_ID_CACHE = {"value": None, "expires": 0.0}
_BUILD_ID_TTL = 1800          # 30 წუთი
DESC_LIMIT = 1500             # აღწერის შენახვის ლიმიტი
DETAIL_MAX = 60               # მაქსიმუმ რამდენ დეტალს ჩამოვწერთ ერთ ძებნაზე


# ─────────────────────────────────────────────────────────────
# buildId
# ─────────────────────────────────────────────────────────────
def _get_build_id(session: requests.Session, force: bool = False) -> Optional[str]:
    now = time.time()
    if not force and _BUILD_ID_CACHE["value"] and _BUILD_ID_CACHE["expires"] > now:
        return _BUILD_ID_CACHE["value"]

    for path in (LIST_PATH, "/ka", "/"):
        try:
            r = session.get(f"{BASE_URL}{path}", timeout=15)
            if r.status_code != 200:
                continue
            m = re.search(r'"buildId"\s*:\s*"([^"]+)"', r.text)
            if not m:
                m = re.search(r'/_next/static/([^/]+)/_buildManifest', r.text)
            if m:
                _BUILD_ID_CACHE["value"] = m.group(1)
                _BUILD_ID_CACHE["expires"] = now + _BUILD_ID_TTL
                return m.group(1)
        except Exception as e:
            log.warning("buildId (%s): %s", path, e)
    return None


# ─────────────────────────────────────────────────────────────
# JSON fetch
# ─────────────────────────────────────────────────────────────
def _fetch_page(session: requests.Session, build_id: str,
                term: str, page: int = 1) -> Optional[dict]:
    url = f"{BASE_URL}/_next/data/{build_id}/ka/l/vacancies.json"
    params = {"searchString": term}
    if page > 1:
        params["page"] = page

    headers = {
        "Accept": "*/*",
        "Referer": f"{BASE_URL}{LIST_PATH}?searchString={term}",
        "x-nextjs-data": "1",
        "x-client-navigation": "true",
    }
    try:
        r = session.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (404, 410):
            _BUILD_ID_CACHE["value"] = None
    except Exception as e:
        log.warning("fetch p%s '%s': %s", page, term, e)
    return None


# ─────────────────────────────────────────────────────────────
# Recursive JSON walker
# ─────────────────────────────────────────────────────────────
_TITLE_KEYS = ("title", "position", "name", "vacancyName")
_ID_KEYS    = ("id", "vacancyId", "uuid", "announcementId")


def _looks_like_vacancy(d: dict) -> bool:
    if not isinstance(d, dict):
        return False
    has_title = any(d.get(k) for k in _TITLE_KEYS)
    has_id    = any(d.get(k) for k in _ID_KEYS)
    return has_title and has_id


def _walk_vacancies(obj, found: list, seen_ids: set, depth: int = 0):
    """რეკურსიულად ვეძებთ ვაკანსიებს ნებისმიერ სიღრმეზე."""
    if depth > 8:
        return
    if isinstance(obj, list):
        for item in obj:
            if _looks_like_vacancy(item):
                vid = next((item.get(k) for k in _ID_KEYS if item.get(k)), None)
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    found.append(item)
            else:
                _walk_vacancies(item, found, seen_ids, depth + 1)
    elif isinstance(obj, dict):
        for key in ("vacancies", "items", "data", "results", "list",
                    "announcements", "content", "pageProps"):
            if key in obj:
                _walk_vacancies(obj[key], found, seen_ids, depth + 1)
        for v in obj.values():
            if isinstance(v, (list, dict)):
                _walk_vacancies(v, found, seen_ids, depth + 1)


def _extract_vacancies(data: dict) -> list:
    if not isinstance(data, dict):
        return []
    found: list = []
    _walk_vacancies(data, found, set())
    return found


# ─────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────
def _pick(d: dict, *keys, default=""):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return default


def _parse_item(item: dict) -> Optional[Job]:
    try:
        vid = next((item.get(k) for k in _ID_KEYS if item.get(k)), None)
        title = next((item.get(k) for k in _TITLE_KEYS if item.get(k)), "")
        title = str(title).strip()
        if not vid or not title:
            return None

        company = _pick(item, "companyName", "customerName", "employerName")
        if not company and isinstance(item.get("company"), dict):
            company = item["company"].get("name", "")

        location = _pick(item, "city", "location", "locationName", "address")
        if isinstance(item.get("location"), dict):
            location = item["location"].get("name", "") or location
        if isinstance(item.get("cities"), list) and item["cities"]:
            location = ", ".join(
                c if isinstance(c, str) else (c.get("name") or "")
                for c in item["cities"]
            ).strip(", ")
        if not location and isinstance(item.get("locations"), list):
            location = ", ".join(str(x) for x in item["locations"])

        remote = bool(
            item.get("isRemote")
            or item.get("isWorkFromHome")
            or item.get("remote")
            or (isinstance(location, str) and "remote" in location.lower())
        )

        slug = item.get("slug") or item.get("seoUrl") or vid
        url = f"{BASE_URL}/ka/l/vacancy/{slug}"

        return Job(
            source="jobs.ss.ge",
            title=title,
            url=url,
            company=str(company).strip(),
            location=str(location).strip() or "საქართველო",
            posted=str(_pick(item, "publishDate", "createdAt", "postedDate")),
            deadline=str(_pick(item, "deadlineDate", "expiresAt", "endDate")),
            salary=str(_pick(item, "salary", "salaryFrom", "salaryTo")),
            remote=remote,
            description="",
        )
    except Exception as e:
        log.warning("parse: %s", e)
        return None


# ─────────────────────────────────────────────────────────────
# Detail fetch — description-ისთვის (filters.py-ს სჭირდება!)
# ─────────────────────────────────────────────────────────────
_STRIP_RE = re.compile(r"<[^>]+>")


def _fetch_description(session: requests.Session, job: Job) -> str:
    """ჩამოტვირთავს ვაკანსიის გვერდს და ამოიღებს ტექსტს."""
    try:
        r = session.get(job.url, timeout=15)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")

        # Next.js __NEXT_DATA__ — ყველაზე სუფთა წყარო
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                nd = json.loads(script.string)
                found: list = []
                _walk_vacancies(nd, found, set())
                if found:
                    d = found[0]
                    desc = _pick(d, "description", "jobDescription", "body", "text")
                    if desc:
                        return _STRIP_RE.sub(" ", str(desc))[:DESC_LIMIT]
            except Exception:
                pass

        # fallback: მთავარი კონტენტის div-ები
        for sel in ("div.vacancy-description",
                    "div.job-description",
                    "div[class*='description']",
                    "main", "article"):
            el = soup.select_one(sel)
            if el:
                text = el.get_text(" ", strip=True)
                if len(text) > 80:
                    return text[:DESC_LIMIT]
    except Exception as e:
        log.warning("desc %s: %s", job.url, e)
    return ""


# ─────────────────────────────────────────────────────────────
# მთავარი scrape
# ─────────────────────────────────────────────────────────────
def _fetch_descriptions(session: requests.Session, jobs: list[Job]) -> None:
    """პარალელურად ჩამოტვირთავს აღწერებს (bounded pool)."""
    if not jobs:
        return
    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as pool:
        futures = {pool.submit(_fetch_description, session, job): job
                   for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            desc = future.result()
            if desc:
                job.description = desc


def scrape(search_terms: Optional[list[str]] = None,
           progress_callback=None) -> list[Job]:
    search_terms = search_terms or ["junior"]
    all_jobs: list[Job] = []

    session = build_session()
    try:
        session.get(f"{BASE_URL}{LIST_PATH}", timeout=15)
    except Exception:
        pass

    build_id = _get_build_id(session)
    if not build_id:
        log.warning("jobs.ss.ge: buildId ვერ მოიძებნა")
        return all_jobs
    log.info("jobs.ss.ge buildId: %s", build_id)

    seen_urls: set[str] = set()

    for i, term in enumerate(search_terms):
        if progress_callback:
            progress_callback(i, len(search_terms), f"jobs.ss.ge: '{term}'")

        term_jobs: list[Job] = []

        # ── პაგინაცია ──
        for page in (1, 2):
            data = _fetch_page(session, build_id, term, page)

            if data is None and _BUILD_ID_CACHE["value"] is None:
                build_id = _get_build_id(session, force=True)
                if build_id:
                    data = _fetch_page(session, build_id, term, page)

            if not data:
                break

            items = _extract_vacancies(data)
            if not items:
                break

            for item in items:
                job = _parse_item(item)
                if job and job.url not in seen_urls:
                    seen_urls.add(job.url)
                    term_jobs.append(job)

            if len(items) < 10:
                break
            time.sleep(REQUEST_DELAY)

        # ── description-ის ჩამოტვირთვა (პარალელურად) ──
        _fetch_descriptions(session, term_jobs[:DETAIL_MAX])

        log.info("jobs.ss.ge '%s': %s ვაკანსია (%s აღწერით)",
                 term, len(term_jobs),
                 sum(1 for j in term_jobs if j.description))
        all_jobs.extend(term_jobs)

    return all_jobs