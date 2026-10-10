"""
JobSpy scraper — მრავალ-რეგიონიანი ძებნა.

"Worldwide" არ მუშაობს jobspy-ში → ვძებნით რამდენიმე ქვეყანაში ცალ-ცალკე
და შედეგებს ვაერთიანებთ.
"""
from jobspy import scrape_jobs as jobspy_scrape
from models import Job
from config import JOBSPY_SITES, JOBSPY_REGIONS


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


def scrape(search_terms=None, results_wanted=25, hours_old=168,
           progress_callback=None, sites=None, regions=None):
    search_terms = search_terms or ["junior"]
    sites = sites or JOBSPY_SITES
    regions = regions or JOBSPY_REGIONS

    all_jobs = []
    seen_urls = set()

    total_steps = len(search_terms) * len(regions)
    step = 0

    for term in search_terms:
        for region in regions:
            step += 1
            if progress_callback:
                progress_callback(step, total_steps,
                                  f"jobspy: '{term}' @ {region}")

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
                print(f"     ✗ jobspy '{term}' @ {region}: {e}")
                continue

            if df is None or df.empty:
                continue

            added = 0
            for _, row in df.iterrows():
                job = _row_to_job(row, str(row.get("site", "?") or "?"))
                if not job.url or job.url in seen_urls or not job.title:
                    continue
                seen_urls.add(job.url)
                all_jobs.append(job)
                added += 1

            if added:
                print(f"     ✓ '{term}' @ {region}: {added}")

    return all_jobs