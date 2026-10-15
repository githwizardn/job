"""
JobSpy scraper — მრავალ-რეგიონიანი ძებნა.

"Worldwide" არ მუშაობს jobspy-ში → ვძებნით რამდენიმე ქვეყანაში ცალ-ცალკე
და შედეგებს ვაერთიანებთ.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from jobspy import scrape_jobs as jobspy_scrape

from logging_utils import get_logger
from models import Job
from config import JOBSPY_SITES, JOBSPY_REGIONS

log = get_logger(__name__)

# პარალელური რეგიონების რაოდენობა (rate-limit-ის თავიდან ასაცილებლად ზომიერი)
MAX_WORKERS = 3

# remote-ის სიგნალები ლოკაციაში
_REMOTE_HINTS = ("remote", "anywhere", "worldwide", "distributed", "home")


def _row_to_job(row, site_name: str) -> Job:
    loc = str(row.get("location", "") or "").strip()
    loc_lower = loc.lower()

    # remote მხოლოდ მაშინ თუ:
    #   (a) jobspy ამბობს is_remote=True, ან
    #   (b) ლოკაცია შეიცავს "remote"/"anywhere"/"worldwide"
    remote_flag = bool(row.get("is_remote", False))
    remote_hint = any(h in loc_lower for h in _REMOTE_HINTS)

    return Job(
        source=f"jobspy-{site_name}",
        title=str(row.get("title", "") or "").strip(),
        url=str(row.get("job_url", "") or "").strip(),
        company=str(row.get("company", "") or "").strip(),
        location=loc,
        posted=str(row.get("date_posted", "") or ""),
        remote=remote_flag or remote_hint,
        description=str(row.get("description", "") or "")[:2000],
    )


def _scrape_one(term: str, region: str, sites: list[str],
                results_wanted: int, hours_old: int) -> list[Job]:
    """ერთი (ტერმინი, რეგიონი) წყვილის ძებნა."""
    try:
        df = jobspy_scrape(
            site_name=sites,
            search_term=term,
            location=region,
            results_wanted=results_wanted,
            hours_old=hours_old,
            is_remote=True,
            verbose=0,
        )
    except Exception as e:
        log.warning("jobspy '%s' @ %s: %s", term, region, e)
        return []

    if df is None or df.empty:
        return []

    jobs: list[Job] = []
    for _, row in df.iterrows():
        job = _row_to_job(row, str(row.get("site", "?") or "?"))
        if job.url and job.title:
            jobs.append(job)
    if jobs:
        log.info("jobspy '%s' @ %s: %s", term, region, len(jobs))
    return jobs


def scrape(search_terms: Optional[list[str]] = None, results_wanted: int = 25,
           hours_old: int = 168, progress_callback=None,
           sites: Optional[list[str]] = None,
           regions: Optional[list[str]] = None) -> list[Job]:
    search_terms = search_terms or ["junior"]
    sites = sites or JOBSPY_SITES
    regions = regions or JOBSPY_REGIONS

    pairs = [(term, region) for term in search_terms for region in regions]
    total_steps = len(pairs)
    all_jobs: list[Job] = []
    seen_urls: set[str] = set()
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(_scrape_one, term, region, sites,
                        results_wanted, hours_old): (term, region)
            for term, region in pairs
        }
        for future in as_completed(futures):
            term, region = futures[future]
            done += 1
            if progress_callback:
                progress_callback(done, total_steps,
                                  f"jobspy: '{term}' @ {region}")
            for job in future.result():
                if job.url in seen_urls:
                    continue
                seen_urls.add(job.url)
                all_jobs.append(job)

    return all_jobs