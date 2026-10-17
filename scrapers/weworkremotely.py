"""WeWorkRemotely — RSS Feed პარსინგი."""
import re
from bs4 import BeautifulSoup
import requests
from models import Job
from logging_utils import get_logger

log = get_logger(__name__)
RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

def scrape(search_terms=None, progress_callback=None):
    search_terms = search_terms or ["developer"]
    all_jobs = []
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(RSS_URL, headers=headers, timeout=15)
        
        if r.status_code != 200:
            log.warning(f"WeWorkRemotely HTTP {r.status_code}")
            return []

        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")

        for item in items:
            title_text = item.find("title").text if item.find("title") else ""
            link = item.find("link").text if item.find("link") else ""
            region = item.find("region").text if item.find("region") else "Worldwide"
            desc_html = item.find("description").text if item.find("description") else ""
            
            # ტექსტის გასუფთავება HTML-ისგან
            desc_soup = BeautifulSoup(desc_html, "html.parser")
            desc = desc_soup.get_text(" ", strip=True)

            # სათაური ხშირად ასე მოდის: "Company Name: Job Title"
            title = title_text.split(":")[-1].strip() if ":" in title_text else title_text
            company = title_text.split(":")[0].strip() if ":" in title_text else ""

            if not any(term.lower() in title.lower() for term in search_terms):
                continue

            all_jobs.append(Job(
                source="weworkremotely",
                title=title,
                url=link,
                company=company,
                location=region,
                posted="",
                remote=True,
                description=desc[:2000],
            ))
            
        log.info(f"weworkremotely: {len(all_jobs)} ვაკანსია")
    except Exception as e:
        log.exception(f"weworkremotely შეცდომა: {e}")
        
    return all_jobs