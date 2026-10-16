"""
ვაკანსიების ფილტრაცია — საქართველოს პერსპექტივიდან.

მოთხოვნა:
  • საქართველოში (onsite / hybrid / remote) → KEEP
  • საზღვარგარეთ + remote + საქართველოდან მუშაობა → KEEP
  • US/UK/EU-only, onsite-abroad → REMOVE

KEEP სიგნალები (უცხო remote-ისთვის):
  - worldwide / anywhere / global
  - EMEA / Europe / Caucasus
  - contractor / B2B / EOR
"""
import re
from typing import Optional

from models import Job
from config import (
    GEORGIAN_LOCATIONS,
    FOREIGN_PLACES,
    RESTRICTED_KEYWORDS,
    GLOBAL_KEYWORDS,
    CONTRACTOR_SIGNALS,
    REMOTE_HINTS,
    GENERIC_REMOTE,
    REGION_SIGNALS,
    US_ONLY_COMPANIES,
    US_ONLY_STRICT,
    TERM_SYNONYMS,
)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
_REMOTE_HINTS = REMOTE_HINTS
_GENERIC_REMOTE = GENERIC_REMOTE
_REGION_SIGNALS = REGION_SIGNALS
_US_ONLY_COMPANIES = US_ONLY_COMPANIES


def _extract_words(term: str) -> list[str]:
    words = re.findall(r"[a-zA-Zა-ჰ0-9]+", term.lower())
    long_words = [w for w in words if len(w) >= 3]
    return long_words if long_words else [term.lower()]


def _expand_term(term: str) -> list[str]:
    """აბრუნებს [სინონიმები...] ან [ორიგინალი] თუ სინონიმი არ აქვს."""
    key = term.lower().strip()
    syns = TERM_SYNONYMS.get(key)
    if syns:
        return syns
    return [term]


def matches_search(job: Job, search_terms: list[str]) -> bool:
    """სათაურსა და კომპანიაში ტერმინების/სინონიმების დამთხვევა."""
    if not search_terms:
        return True

    haystack = f"{job.title} {job.company}".lower()

    for term in search_terms:
        variants = _expand_term(term)
        for variant in variants:
            v = variant.lower().strip()

            # მრავალსიტყვიანი ფრაზა — substring
            if " " in v and len(v) >= 5 and v in haystack:
                return True

            # ერთი სიტყვა — მხოლოდ სიტყვის საზღვრებით (word boundary)
            for w in _extract_words(v):
                if _has_word(haystack, w):
                    return True

    return False


def _has_word(text: str, word: str) -> bool:
    """სიტყვის საზღვრებით დამთხვევა (unicode-safe ქართულისთვის)."""
    if not word:
        return False
    pattern = rf"(?<![\w]){re.escape(word)}(?![\w])"
    return bool(re.search(pattern, text, re.UNICODE))


def _find_foreign(loc: str) -> Optional[str]:
    for place in FOREIGN_PLACES:
        if _has_word(loc, place):
            return place
    return None


def _find_georgian(loc: str) -> Optional[str]:
    for geo in GEORGIAN_LOCATIONS:
        if _has_word(loc, geo):
            return geo
    return None


def _find_global_signal(loc: str, desc: str) -> Optional[str]:
    for kw in GLOBAL_KEYWORDS:
        if kw in loc or kw in desc:
            return kw
    return None


def _has_region_signal(loc: str, desc: str) -> str:
    text = f"{loc} {desc}"
    for sig in _REGION_SIGNALS:
        if sig in text:
            return sig
    return ""


def _has_contractor_signal(desc: str) -> bool:
    head = desc[:3000]
    return any(sig in head for sig in CONTRACTOR_SIGNALS)


def _is_remote(job: Job, loc: str, desc: str) -> bool:
    if job.remote:
        return True
    if any(h in loc for h in _REMOTE_HINTS):
        return True
    head = desc[:600]
    if any(h in head for h in _REMOTE_HINTS):
        return True
    return False


def _is_us_only_company(job: Job) -> str:
    """აბრუნებს კომპანიის სახელს თუ US-only blacklist-შია."""
    company_lower = (job.company or "").lower()
    if not company_lower:
        return ""
    for us_co in _US_ONLY_COMPANIES:
        if us_co in US_ONLY_STRICT:
            if _has_word(company_lower, us_co):
                return us_co
        elif us_co in company_lower:
            return us_co
    return ""


# ─────────────────────────────────────────────────────────────
# მთავარი შემოწმება
# ─────────────────────────────────────────────────────────────
def is_available_from_georgia(job: Job) -> tuple[bool, str]:
    """
    Returns: (available: bool, reason: str)
    """
    loc = (job.location or "").lower().strip()
    desc = (job.description or "").lower()

    # ─── 1. მკაცრი შეზღუდვა აღწერაში ───
    for kw in RESTRICTED_KEYWORDS:
        if kw in desc:
            return False, f"⛔ {kw}"

    # ─── 2. ქართული ლოკაცია → KEEP ───
    geo = _find_georgian(loc)
    if geo:
        return True, f"🇬🇪 {geo}"

    # ─── 3. US-only კომპანია → REMOVE ───
    us_co = _is_us_only_company(job)
    if us_co:
        return False, f"🇺🇸 {us_co}"

    # ─── 4. უცხო ლოკაცია ───
    foreign = _find_foreign(loc)
    if foreign:
        is_remote = _is_remote(job, loc, desc)

        # 4a. უცხო + onsite → REMOVE
        if not is_remote:
            return False, f"📍 {foreign} (onsite)"

        # 4b. remote + worldwide/anywhere → KEEP
        gk = _find_global_signal(loc, desc)
        if gk:
            if any(r in gk for r in _REGION_SIGNALS):
                return True, f"🌍 {foreign} + {gk} (region)"
            return True, f"🌍 {foreign} + {gk}"

        # 4c. remote + EMEA/Europe/Caucasus → KEEP
        region = _has_region_signal(loc, desc)
        if region:
            return True, f"🌍 {foreign} + {region}"

        # 4d. remote + contractor → KEEP
        if _has_contractor_signal(desc):
            return True, f"💼 {foreign} + contractor"

        # 4e. remote, სიგნალის გარეშე → REMOVE
        return False, f"📍 {foreign} (remote, no worldwide)"

    # ─── 5. ცარიელი / generic remote ───
    gk = _find_global_signal(loc, desc)
    if gk:
        return True, f"🌍 {gk}"

    if loc in _GENERIC_REMOTE or not loc:
        return True, "🌐 generic remote"

    # ─── 6. ვერ გადავწყვიტეთ ───
    # თუ ლოკაცია აშკარად ქალაქია (არა remote), REMOVE
    if loc and not any(h in loc for h in _REMOTE_HINTS):
        return False, f"❓ {loc[:30]} (onsite)"
    return True, f"❓ {loc[:30]}"


# ─────────────────────────────────────────────────────────────
# Batch ფილტრი
# ─────────────────────────────────────────────────────────────
def filter_jobs(jobs: list[Job], search_terms: list[str]) -> tuple[list[Job], dict]:
    kept = []
    stats = {
        "total": len(jobs),
        "title_removed": 0,
        "geo_removed": 0,
        "kept": 0,
        "geo_reasons": {},
        "title_samples": [],
    }

    for job in jobs:
        if not matches_search(job, search_terms):
            stats["title_removed"] += 1
            if len(stats["title_samples"]) < 8:
                stats["title_samples"].append(job.title)
            continue

        available, reason = is_available_from_georgia(job)
        if available:
            job.geo_status = reason
            kept.append(job)
            stats["kept"] += 1
        else:
            stats["geo_removed"] += 1
            stats["geo_reasons"][reason] = stats["geo_reasons"].get(reason, 0) + 1

    return kept, stats