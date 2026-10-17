import os
from pathlib import Path

from dotenv import load_dotenv

# ჩატვირთე .env ფაილი (თუ არსებობს)
load_dotenv(Path(__file__).parent / ".env")

# ============================================================
# JobRadar — კონფიგურაცია
# ============================================================

# --- ზოგადი ---
OUTPUT_DIR = "output"
OUTPUT_FILE = "all_jobs.csv"
MY_TERMS_FILE = "my_terms.json"
REQUEST_DELAY = 2
RESULTS_PER_SEARCH = 25
HOURS_OLD = 168

# HTTP retry პარამეტრები
HTTP_RETRIES = 3
HTTP_BACKOFF = 0.5

DETAIL_WORKERS = 4

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# --- jobspy-ს წყაროები ---
JOBSPY_SITES = ["linkedin", "indeed", "google", "glassdoor"]

# --- jobspy-ს რეგიონები ---
JOBSPY_REGIONS = [
    "Tbilisi",           # ← ქართული ვაკანსიები LinkedIn-ზე
    "Georgia",           # ← ზოგადი "Georgia" (ხშირად აშშ-ის შტატია, მაგრამ ვცადოთ)
    "United States",
    "United Kingdom",
    "Germany",
    "Netherlands",
    "Cyprus",
]

# --- აქტიური სქრაპერები ---
ENABLED_SCRAPERS = [
    "jobspy",
    "jobs_ge",
    "hr_ge",
    "remotive",
    "remoteok",         # ← ახალი
    "weworkremotely",
]

# ============================================================
# ფილტრაციის სიტყვები
# ============================================================

# 🏠 ქართული ლოკაციები — თუ აქ არის, ვაკანსია რჩება
GEORGIAN_LOCATIONS = [
    "tbilisi", "batumi", "kutaisi", "rustavi", "gori", "zugdidi",
    "telavi", "poti", "ozurgeti", "kvemo kartli",
    "თბილისი", "ბათუმი", "ქუთაისი", "რუსთავი", "გორი", "ზუგდიდი",
    "თელავი", "ფოთი", "ოზურგეთი",
     "საქართველო",
]

# 🌍 უცხო ქვეყნები/ქალაქები — თუ ლოკაციაშია (და არ არის remote) → REMOVE
FOREIGN_PLACES = [
    # ქვეყნები
    "united states", "usa", "u.s.", "u.s.a.", "america",
    "canada", "united kingdom", "uk", "england", "britain", "scotland",
    "ireland", "germany", "france", "spain", "italy", "portugal",
    "netherlands", "belgium", "switzerland", "austria", "sweden",
    "norway", "denmark", "finland", "poland", "czech", "hungary",
    "romania", "bulgaria", "greece", "croatia", "serbia", "slovakia",
    "slovenia", "estonia", "latvia", "lithuania", "ukraine", "russia",
    "india", "pakistan", "bangladesh", "sri lanka", "nepal",
    "china", "japan", "korea", "vietnam", "thailand", "indonesia",
    "malaysia", "singapore", "philippines", "taiwan", "hong kong",
    "turkey", "israel", "uae", "dubai", "saudi arabia", "qatar",
    "egypt", "australia", "new zealand", "south africa", "nigeria",
    "kenya", "brazil", "argentina", "chile", "colombia", "peru", "mexico",
    "cyprus", "malta", "luxembourg", "iceland",
    # მთავარი ქალაქები
    "london", "paris", "berlin", "madrid", "rome", "amsterdam",
    "barcelona", "munich", "vienna", "prague", "warsaw", "stockholm",
    "copenhagen", "oslo", "helsinki", "dublin", "brussels", "zurich",
    "tokyo", "osaka", "seoul", "beijing", "shanghai", "bangkok",
    "jakarta", "manila", "mumbai", "delhi", "bangalore", "hyderabad",
    "chennai", "pune", "sydney", "melbourne", "auckland",
    "toronto", "vancouver", "montreal",
    "new york", "san francisco", "los angeles", "chicago", "boston",
    "seattle", "austin", "denver", "atlanta", "miami", "dallas",
    "houston", "philadelphia", "washington", "olathe", "kansas",
    "limassol", "nicosia", "larnaca", "paphos",
    "cracow", "krakow", "wroclaw", "lisbon", "porto",
    "omaha", "limassol municipality",
]

# ⛔ აკრძალვები აღწერაში — თუ რომელიმე ეს არის → REMOVE (უპირობოდ)
RESTRICTED_KEYWORDS = [
    # US-only
    "us only", "usa only", "u.s. only", "united states only",
    "must be located in the us", "must reside in the us",
    "must be in the us", "must be based in the us",
    "us-based only", "usa-based only", "us residents only",
    "authorized to work in the us", "us work authorization",
    "must be authorized to work in the us",
    "right to work in the us", "us citizen", "us citizenship",
    "green card", "us work permit", "only us candidates",
    "us-based candidates only",
    # UK-only
    "uk only", "must be uk", "must be based in the uk",
    "must reside in the uk", "right to work in the uk",
    "british citizens", "uk-based candidates only",
    # EU-only (Georgia NOT in EU)
    "eu only", "eu-based only", "eu citizens", "european union only",
    "must be in the eu", "must reside in the eu",
    "must be based in the eu", "eu member states only",
    "eu work permit required", "eu work authorization",
    # კონკრეტული ქვეყნები
    "canada only", "must be based in canada", "canadian citizens",
    "australia only", "must be based in australia",
    "india only", "must be based in india",
    "germany only", "must be based in germany",
    "netherlands only", "must be based in netherlands",
    "poland only", "must be based in poland",
    "cyprus only", "must be based in cyprus",
    # Visa/Authorization
    "no visa sponsorship", "we do not sponsor visas",
    "we are unable to sponsor",
    "security clearance", "ts/sci", "top secret",
    # Timezone
    "must work est hours", "must work pst hours",
    "must work cst hours", "must work mst hours",
    "must be in est timezone", "must be in pst timezone",
    "us timezone required", "us time zone required",
    "americas timezone only", "american timezone only",
    "must overlap with us hours",
]

# ✅ ნებადართული ფრაზები — თუ რომელიმე ეს არის → KEEP
GLOBAL_KEYWORDS = [
    # Worldwide / anywhere
    "worldwide", "world-wide", "world wide",
    "anywhere", "work from anywhere", "work from any location",
    "remote worldwide", "fully remote worldwide",
    "no location restriction", "no geographical restriction",
    "location independent", "location agnostic",
    "from any country", "any country",
    "international candidates", "international applicants",
    "open globally", "anywhere in the world",
    # EMEA / Europe / Caucasus
    "emea", "europe", "european", "european region",
    "caucasus", "caucasian region",
    "eastern europe", "central europe",
    # Global team
    "global team", "global company", "global remote",
    "international team", "distributed team",
    # Contractor
    "contractor", "b2b", "freelance",
    "employer of record", "eor",
    "independent contractor",
    "work as contractor",
]

# 💼 Contractor სიგნალები
CONTRACTOR_SIGNALS = [
    "contractor", "b2b", "freelance", "eor",
    "employer of record", "independent contractor",
    "fixed price", "hourly rate", "monthly retainer",
]

# ============================================================
# ფილტრაციის დამხმარე სიტყვები (filters.py-დან გადმოტანილი)
# ============================================================

# remote-ის სიგნალები
REMOTE_HINTS = (
    "remote", "რემოუტ", "დისტანციურ",
    "work from home", "wfh", "telecommute",
)

# ცარიელი / ზოგადი remote ლოკაციები
# (worldwide / anywhere / global უკვე GLOBAL_KEYWORDS-შია)
GENERIC_REMOTE = {
    "", "remote", "fully remote", "remote job", "remote position",
    "remote work", "100% remote", "remote - remote",
}

# რეგიონალური სიგნალები
REGION_SIGNALS = (
    "emea", "europe", "european", "caucasus",
    "eastern europe", "central europe", "eurasia",
)

# US-only კომპანიების blacklist (defense, government, insurance)
US_ONLY_COMPANIES = {
    "lockheed martin", "caci", "caci international", "lmi",
    "tista", "leidos", "booz allen", "saic",
    "northrop grumman", "raytheon", "gdit", "mantech",
    "voya financial", "farmers insurance", "amgen",
    "associated bank", "general dynamics", "bae systems",
    "mitre", "parsons", "peraton", "jacobs",
}

# მოკლე ჩანაწერები, რომლებსაც მკაცრი სიტყვის-საზღვრის შემოწმება სჭირდება
US_ONLY_STRICT = {
    "caci", "lmi", "tista", "saic", "gdit", "mitre",
}




# ============================================================
# Telegram (უფასო შეტყობინებები)
# ============================================================
# ლოკალურად ტესტისთვის შეგიძლია პირდაპირ ჩაწერო, მაგრამ ჯობია env-ცვლადებით:
#   Windows CMD:   set TELEGRAM_BOT_TOKEN=...
#   Windows PS:    $env:TELEGRAM_BOT_TOKEN="..."
#   bash:          export TELEGRAM_BOT_TOKEN="..."
# GitHub Actions: Repository Secrets (მოგვიანებით)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")




# ============================================================
# ტერმინების სინონიმები — ძებნა ჭკვიანური რომ იყოს
# ============================================================
# "frontend" რომ ეძებო, "React Developer"-იც მოიძებნოს
TERM_SYNONYMS = {
    "frontend": [
        "frontend", "front-end", "front end",
        "react", "vue", "angular", "next.js", "svelte",
    ],
    "react": [
        "react", "react.js", "reactjs",
    ],
    "react native": [
        "react native", "react-native", "reactnative",
    ],
    "javascript": [
        "javascript", "ecmascript", "es6", "typescript",
    ],
    "web developer": [
        "web developer", "web dev", "fullstack", "full-stack",
        "full stack", "web development",
    ],
    "junior developer": [
        "junior", "jr ", "jr.", "entry level", "entry-level",
        "junior developer", "junior frontend",
    ],
    "it support": [
        "it support", "helpdesk", "help desk", "service desk",
        "technical support", "tech support", "it specialist",
        "sysadmin", "system administrator", "it technician",
    ],
    "customer support": [
        "customer support", "customer service", "client service",
        "client support", "customer success", "call center",
    ],
    "network": [
        "network", "networking", "network engineer", "network admin",
        "network administrator", "ccna", "cisco", "noc",
    ],
    "cybersecurity": [
        "cybersecurity", "cyber security", "information security",
        "infosec", "security analyst", "soc analyst", "security engineer",
    ],
    "intern": [
        "intern", "internship", "trainee", "სტაჟიორი",
    ],
    "სტაჟიორი": [
        "intern", "internship", "trainee", "junior", "სტაჟიორი",
    ],
}