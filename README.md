# 🎯 JobRadar

ვაკანსიების აგრეგატორი — ავტომატურად ეძებს სამსახურებს სხვადასხვა წყაროდან, ფილტრავს გეოგრაფიულად და აგზავნის Telegram-ზე.

## ✨ ფუნქციები

- 🔍 **4 წყარო:** LinkedIn, Indeed, Glassdoor, Google (jobspy-ით), jobs.ge, hr.ge, Remotive
- 🌍 **გეო-ფილტრი:** მხოლოდ საქართველოდან ხელმისაწვდომი ვაკანსიები
- 🔄 **დედუპლიკაცია:** URL + (title + company) — ერთს არ იმეორებს
- 💾 **SQLite ბაზა:** ინახავს ისტორიას, ახსოვს რა ნახა
- ⭐ **ქულით დალაგება:** ყველაზე რელევანტური პირველ ადგილზე
- 📱 **Telegram შეტყობინება:** ახალი ვაკანსიები ტელეფონზე
- 🤖 **ავტომატური გაშვება:** GitHub Actions, დღეში 2-ჯერ
- 📊 **ისტორიის გვერდი:** tracking (✅ მიმართული, ⭐ ფავორიტი), CSV ექსპორტი
- 🖥️ **Streamlit UI:** ვიზუალური ინტერფეისი

## 🚀 დაყენება

    git clone https://github.com/githwizardn/job.git
    cd job
    python -m venv venv

    # Windows
    venv\Scripts\activate

    # macOS/Linux
    source venv/bin/activate

    pip install -r requirements.txt

## ⚙️ კონფიგურაცია

### 1. `.env` ფაილი

შექმენი `.env` პროექტის ძირში:

    TELEGRAM_BOT_TOKEN=your_bot_token_here
    TELEGRAM_CHAT_ID=your_chat_id_here

### 2. Telegram Bot

1. Telegram-ში მოძებნე `@BotFather`
2. `/newbot` → სახელი და username
3. დააკოპირე **token** → `.env`-ში
4. გაუშვი bot-ს `/start`
5. `@userinfobot`-იდან აიღე **chat_id** → `.env`-ში

### 3. საძიებო ტერმინები

`my_terms.json` ფაილში ჩაწერე ტერმინები:

    ["frontend", "react", "junior developer", "intern"]

## 🎮 გამოყენება

### CLI (ტერმინალიდან)

    # სრული — ძებნა + Telegram
    python cli.py

    # ტესტი — მხოლოდ ძებნა, Telegram-ის გარეშე
    python cli.py --no-notify

### Streamlit UI

    streamlit run app.py

გაიხსნება ბრაუზერში `http://localhost:8501`.

## 🤖 ავტომატური გაშვება (GitHub Actions)

Workflow უკვე კონფიგურირებულია — დღეში 2-ჯერ (10:00 და 22:00 თბილისით).

**საჭირო ნაბიჯები:**

1. **GitHub Secrets:** Settings → Secrets → Actions
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

2. **Workflow permissions:** Settings → Actions → General
   - ✅ Read and write permissions

3. **ხელით გაშვება:** Actions tab → JobRadar → Run workflow

## 🏗️ არქიტექტურა

    jobradar/
    ├── .github/workflows/
    │   └── jobradar.yml          # GitHub Actions (cron)
    ├── pages/
    │   └── 2_📚_ისტორია.py       # ისტორიის გვერდი
    ├── scrapers/
    │   ├── __init__.py
    │   ├── hr_ge.py              # hr.ge API
    │   ├── jobs_ge.py            # jobs.ge HTML
    │   ├── jobspy_scraper.py     # LinkedIn/Indeed/Glassdoor/Google
    │   └── remotive_scraper.py   # Remotive API
    ├── output/
    │   └── jobradar.log          # ლოგი
    ├── app.py                    # Streamlit UI — ძებნა
    ├── cli.py                    # CLI runner (Actions-ისთვის)
    ├── config.py                 # ყველა პარამეტრი
    ├── db.py                     # SQLite ბაზა
    ├── dedupe.py                 # დედუპლიკაცია
    ├── filters.py                # გეო-ფილტრი + სინონიმები
    ├── http_utils.py             # Session + retry
    ├── logging_utils.py          # logger
    ├── models.py                 # Job dataclass
    ├── my_terms.json             # საძიებო ტერმინები
    ├── notify.py                 # Telegram
    ├── scoring.py                # ქულების სისტემა
    └── requirements.txt

## 🔧 კონფიგურაცია (`config.py`)

| პარამეტრი | აღწერა | ნაგულისხმევი |
|---|---|---|
| `REQUEST_DELAY` | წამები query-ებს შორის | 2 |
| `HTTP_RETRIES` | retry-ს რაოდენობა | 3 |
| `HTTP_BACKOFF` | backoff ფაქტორი | 0.5 |
| `RESULTS_PER_SEARCH` | შედეგები ტერმინზე | 25 |
| `HOURS_OLD` | ბოლო რამდენ საათში | 168 |
| `ENABLED_SCRAPERS` | აქტიური წყაროები | 4 |

### ფილტრაციის პარამეტრები

- `GEORGIAN_LOCATIONS` — ქართული ქალაქები (KEEP სიგნალი)
- `FOREIGN_PLACES` — უცხო ქვეყნები/ქალაქები
- `RESTRICTED_KEYWORDS` — US/EU/UK-only ფრაზები (REMOVE)
- `GLOBAL_KEYWORDS` — worldwide/anywhere/EMEA (KEEP)
- `CONTRACTOR_SIGNALS` — contractor/b2b/freelance (KEEP)
- `US_ONLY_COMPANIES` — კომპანიების blacklist
- `TERM_SYNONYMS` — ტერმინების სინონიმები (frontend → react/vue/angular)

## 📊 მონაცემთა ნაკადი

    1. ძებნა      →  4 scraper (პარალელურად სადაც შესაძლებელია)
    2. Dedupe     →  URL + (title + company)
    3. ფილტრი     →  matches_search + is_available_from_georgia
    4. ბაზა       →  fingerprint-ით upsert (მხოლოდ ახლები)
    5. Telegram   →  ახალი ვაკანსიები ტელეფონზე

## 🧪 როგორ მუშაობს ფილტრი

    1. ⛔ RESTRICTED_KEYWORDS აღწერაში → REMOVE
    2. 🇬🇪 ქართული ლოკაცია → KEEP
    3. 🇺🇸 US-only კომპანია → REMOVE
    4. 📍 უცხო + onsite → REMOVE
    5. 🌍 უცხო + remote + "worldwide" → KEEP
    6. 🌍 უცხო + remote + EMEA → KEEP
    7. 💼 უცხო + remote + contractor → KEEP
    8. 📍 უცხო + remote, სიგნალის გარეშე → REMOVE

## 🛠️ ტექნოლოგიები

- **Python 3.11**
- **requests** — HTTP (Session + retry)
- **BeautifulSoup4** — HTML parsing
- **python-jobspy** — LinkedIn, Indeed, Glassdoor, Google
- **SQLite** — ბაზა (ისტორია, tracking)
- **Streamlit** — UI
- **python-dotenv** — კონფიგურაცია
- **GitHub Actions** — ავტომატიზაცია (cron)

## 📦 requirements.txt

    streamlit>=1.30.0
    pandas>=2.0.0
    requests>=2.31.0
    beautifulsoup4>=4.12.0
    python-jobspy>=1.1.0
    lxml>=5.0.0
    python-dotenv>=1.0.0

## 🔐 უსაფრთხოება

- `.env` ფაილი `.gitignore`-შია — GitHub-ზე არ აიტვირთება
- Telegram token ინახება `.env`-ში (ლოკალურად) + GitHub Secrets-ში (დაშიფრული)
- `.env.example` — ნიმუში ცარიელი მნიშვნელობებით

## 📄 ლიცენზია

MIT

## 