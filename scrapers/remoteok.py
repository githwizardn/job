"""RemoteOK — უფასო JSON API."""
import requests
from models import Job
from logging_utils import get_logger

log = get_logger(__name__)
API_URL = "https://remoteok.com/api"

def scrape(search_terms=None, progress_callback=None):
    search_terms = search_terms or ["developer"]
    all_jobs = []
    
    try:
        # RemoteOK მოითხოვს User-Agent-ს, თორემ არ აბრუნებს პასუხს
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(API_URL, headers=headers, timeout=15)
        
        if r.status_code != 200:
            log.warning(f"RemoteOK HTTP {r.status_code}")
            return []

        data = r.json()
        # პირველი ელემენტი ყოველთვის ცარიელია/რეკლამაა, ამიტომ ვტოვებთ
        items = data[1:] if len(data) > 1 else []

        for item in items:
            title = (item.get("position") or "").strip()
            url = (item.get("url") or "").strip()
            
            # ვამოწმებთ, ემთხვევა თუ არა ჩვენს საძიებო ტერმინებს
            if not any(term.lower() in title.lower() for term in search_terms):
                continue

            desc = (item.get("description") or "").strip()
            
            all_jobs.append(Job(
                source="remoteok",
                title=title,
                url=url,
                company=(item.get("company") or "").strip(),
                location=(item.get("location") or "Worldwide").strip(),
                posted=str(item.get("date") or ""),
                salary=str(item.get("salary_min") or ""),
                remote=True,
                description=desc[:2000],
            ))
            
        log.info(f"remoteok: {len(all_jobs)} ვაკანსია")
    except Exception as e:
        log.exception(f"remoteok შეცდომა: {e}")
        
    return all_jobs