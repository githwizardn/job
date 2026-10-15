# JobRadar

ვაკანსიების აგრეგატორი საქართველოდან — აგროვებს ვაკანსიებს ქართული და გლობალური წყაროებიდან, ფილტრავს გეოგრაფიულად.

## ფუნქციები

- jobspy (LinkedIn/Indeed/Glassdoor/Google), jobs.ge, hr.ge + doctor.ge, jobs.ss.ge, Remotive
- გეო-ფილტრი — მხოლოდ ვაკანსიები, სადაც საქართველოდან მუშაობა შესაძლებელია
- Cross-site დედუპლიკაცია
- CSV ექსპორტი

## დაყენება

```bash
git clone https://github.com/gitwizardn/job.git
cd job
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

## არქიტექტურა

```text
app.py           # Streamlit UI + სქრაპერების რეგისტრი
config.py        # ყველა tunable პარამეტრი და საკვანძო სიტყვა
models.py        # Job dataclass
dedupe.py        # URL + cross-site დედუპლიკაცია
filters.py       # გეო-ფილტრაციის ლოგიკა
http_utils.py    # requests.Session retry/backoff-ით
logging_utils.py # საერთო logger (კონსოლი + output/jobradar.log)
scrapers/        # თითო წყარო — თითო მოდული
```

## კონფიგურაცია

ყველა ფილტრი და პარამეტრი [config.py](config.py)-შია:

- `REQUEST_DELAY`, `HTTP_RETRIES`, `HTTP_BACKOFF` — ქსელური ქცევა
- `DETAIL_WORKERS` — jobs.ss.ge აღწერების პარალელური ჩამოტვირთვა
- `GEORGIAN_LOCATIONS`, `FOREIGN_PLACES` — გეო-სიგნალები
- `RESTRICTED_KEYWORDS`, `GLOBAL_KEYWORDS` — KEEP/REMOVE ფრაზები
- `US_ONLY_COMPANIES` — კომპანიების blacklist