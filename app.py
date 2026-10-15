import streamlit as st
import pandas as pd
from datetime import datetime
import importlib
import json
import os

from config import MY_TERMS_FILE, RESULTS_PER_SEARCH, HOURS_OLD
from dedupe import dedupe
from logging_utils import get_logger

log = get_logger("app")

# ============================================================
# გვერდის კონფიგურაცია
# ============================================================
st.set_page_config(
    page_title="JobRadar",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; }
    .sub-header { color: #666; font-size: 1rem; margin-bottom: 1.5rem; }
    .stButton > button { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎯 JobRadar</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ვაკანსიების ძებნა — ქართული და რემოუტ საიტებიდან</div>', unsafe_allow_html=True)


# ============================================================
# შენახვა — ფაილში
# ============================================================
def load_my_terms():
    if os.path.exists(MY_TERMS_FILE):
        try:
            with open(MY_TERMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_my_terms(terms):
    try:
        with open(MY_TERMS_FILE, "w", encoding="utf-8") as f:
            json.dump(terms, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"შენახვის შეცდომა: {e}")


if "my_terms" not in st.session_state:
    st.session_state.my_terms = load_my_terms()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ პარამეტრები")

    # --- სად ვეძებთ ---
    st.subheader("🌐 სად ვეძებთ")
    use_jobspy = st.checkbox("JobSpy (LinkedIn, Indeed, Glassdoor, Google)", value=True)
    use_jobs_ge = st.checkbox("jobs.ge (ქართული)", value=True)
    use_hr_ge = st.checkbox("hr.ge + doctor.ge (API)", value=True)
    use_jobs_ss = st.checkbox("jobs.ss.ge (ქართული)", value=True)
    use_remotive = st.checkbox("Remotive.com (Remote API)", value=True)

    st.divider()

    # --- რა ვეძებთ ---
    st.subheader("🔍 რა ვეძებთ")

    with st.form("add_term_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_term = st.text_input(
                "ტერმინი",
                placeholder="IT Support, Junior, სტაჟიორი...",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("➕")

        if submitted and new_term.strip():
            term = new_term.strip()
            if term not in st.session_state.my_terms:
                st.session_state.my_terms.append(term)
                save_my_terms(st.session_state.my_terms)
                st.rerun()
            else:
                st.warning(f"'{term}' უკვე დამატებულია")

    if st.session_state.my_terms:
        st.caption(f"📊 დამატებული: **{len(st.session_state.my_terms)}**")
        for term in list(st.session_state.my_terms):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"🔵 **{term}**")
            with c2:
                if st.button("❌", key=f"del_{term}", help="წაშალე"):
                    st.session_state.my_terms.remove(term)
                    save_my_terms(st.session_state.my_terms)
                    st.rerun()

        if len(st.session_state.my_terms) > 1:
            if st.button("🗑️ ყველას წაშლა", use_container_width=True):
                st.session_state.my_terms = []
                save_my_terms(st.session_state.my_terms)
                st.rerun()
    else:
        st.info("👆 ჩაწერე ტერმინი და დააჭირე **➕**")

    st.divider()

    # --- გეო ფილტრი ---
    st.subheader("🌍 გეო-ფილტრი")
    geo_filter = st.checkbox(
        "მხოლოდ საქართველოდან ხელმისაწვდომი",
        value=True,
        help="შლის US/EU/UK/India-only და ა.შ. ვაკანსიებს",
    )

    st.divider()

    # --- პარამეტრები ---
    st.subheader("🎛️ დამატებითი")
    results_per = st.slider("შედეგები ტერმინზე", 5, 100, RESULTS_PER_SEARCH, 5)
    hours_old = st.slider("ბოლო რამდენი საათი", 24, 720, HOURS_OLD, 24)

    st.divider()
    run_button = st.button("🚀 ძებნა", type="primary", use_container_width=True)


# ============================================================
# ძებნა
# ============================================================
if run_button:
    selected_terms = st.session_state.my_terms

    if not selected_terms:
        st.error("⚠️ ჯერ არაფერი დაგიმატებია! ჩაწერე ტერმინი და დააჭირე ➕")
        st.stop()

    # ── სქრაპერების რეგისტრი: სახელი → (მოდული, დამატებითი kwargs) ──
    SCRAPER_REGISTRY = {
        "jobspy": ("jobspy_scraper", {"results_wanted": results_per,
                                      "hours_old": hours_old}),
        "jobs_ge": ("jobs_ge", {}),
        "hr_ge": ("hr_ge", {}),
        "jobs_ss_ge": ("jobs_ss_ge", {}),
        "remotive": ("remotive_scraper", {}),
    }

    enabled: list[str] = []
    if use_jobspy: enabled.append("jobspy")
    if use_jobs_ge: enabled.append("jobs_ge")
    if use_hr_ge: enabled.append("hr_ge")
    if use_jobs_ss: enabled.append("jobs_ss_ge")
    if use_remotive: enabled.append("remotive")

    if not enabled:
        st.error("⚠️ აირჩიე მინიმუმ ერთი საიტი!")
        st.stop()

    st.info(f"🔍 ვეძებ {len(selected_terms)} ტერმინს {len(enabled)} საიტზე...")

    with st.expander("👁️ საძიებო ტერმინები", expanded=False):
        st.write(", ".join(selected_terms))

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(current, total, message):
        pct = current / max(total, 1)
        progress_bar.progress(min(pct, 1.0))
        status_text.text(message)

    all_jobs: list = []
    errors: list[str] = []

    for name in enabled:
        module_name, extra = SCRAPER_REGISTRY[name]
        with st.spinner(f"{name} — მიმდინარეობს..."):
            try:
                module = importlib.import_module(f"scrapers.{module_name}")
                jobs = module.scrape(
                    search_terms=selected_terms,
                    progress_callback=update_progress,
                    **extra,
                )
                all_jobs.extend(jobs)
            except Exception as e:
                log.exception("scraper %s failed", name)
                errors.append(f"{name}: {e}")
                with st.expander(f"⚠️ {name} — შეცდომა", expanded=False):
                    st.exception(e)

    progress_bar.progress(1.0)
    status_text.text("✅ ჩამოტვირთვა დასრულდა")

    if errors:
        st.warning("ზოგიერთი სქრაპერი ვერ დასრულდა: " + "; ".join(errors))

    # ─────────────────────────────────────────────────────
    # დედუპლიკაცია: URL + cross-site (title + company)
    # ─────────────────────────────────────────────────────
    if all_jobs:
        all_jobs = dedupe(all_jobs, cross_site=True)

    st.caption(f"📦 უნიკალური ვაკანსიები: **{len(all_jobs)}**")

    # --- ფილტრაცია ---
    filter_stats = None
    if all_jobs and geo_filter:
        with st.spinner("ფილტრაცია..."):
            try:
                from filters import filter_jobs
                before = len(all_jobs)
                all_jobs, filter_stats = filter_jobs(all_jobs, selected_terms)
                after = len(all_jobs)

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("📥 ჩამოტვირთული", before)
                col_b.metric("✅ დარჩა", after)
                col_c.metric("🗑️ გამორიცხული", before - after)

                with st.expander("📊 ფილტრაციის დეტალები"):
                    st.write(f"**🎯 სათაური არ ემთხვეოდა:** {filter_stats['title_removed']}")
                    st.write(f"**📍 გეო-შეზღუდვა:** {filter_stats['geo_removed']}")

                    if filter_stats["title_samples"]:
                        st.write("**გამორიცხული სათაურის მაგალითები:**")
                        for t in filter_stats["title_samples"][:5]:
                            st.write(f"  ❌ {t}")

                    if filter_stats["geo_reasons"]:
                        st.write("**გეო-მიზეზები:**")
                        for reason, count in sorted(
                            filter_stats["geo_reasons"].items(),
                            key=lambda x: -x[1]
                        ):
                            st.write(f"  **{count}×** {reason}")
            except Exception as e:
                log.exception("filter failed")
                with st.expander("⚠️ ფილტრაციის შეცდომა", expanded=False):
                    st.exception(e)
    elif all_jobs and not geo_filter:
        from filters import matches_search
        before = len(all_jobs)
        all_jobs = [j for j in all_jobs if matches_search(j, selected_terms)]
        st.caption(f"🔎 გეო-ფილტრი გამორთულია — სათაურით გაფილტრვა: {before} → {len(all_jobs)}")

    # --- შენახვა ---
    if all_jobs:
        df = pd.DataFrame([j.to_dict() for j in all_jobs])
        df = df.sort_values("source").reset_index(drop=True)
        st.session_state["results"] = df
        st.session_state["search_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        st.session_state["results"] = None
        st.session_state["search_time"] = ""
        st.warning("❌ ვერაფერი მოიძებნა. სცადე სხვა ტერმინები ან გამორთე გეო-ფილტრი.")


# ============================================================
# შედეგები
# ============================================================
if st.session_state.get("results") is not None:
    df = st.session_state["results"]

    st.success(f"✅ ნაპოვნია **{len(df)}** უნიკალური ვაკანსია")
    st.caption(f"ძებნის დრო: {st.session_state.get('search_time', '')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("სულ", len(df))
    c2.metric("წყაროები", df["source"].nunique())
    c3.metric("რემოუტ", int(df["remote"].sum()) if "remote" in df.columns else 0)
    c4.metric("კომპანიები", df["company"].replace("", pd.NA).dropna().nunique())

    st.divider()

    # --- დამატებითი ფილტრები ---
    st.subheader("🔎 დამატებითი ფილტრები")
    fc1, fc2, fc3 = st.columns([2, 2, 3])

    with fc1:
        sources = sorted(df["source"].unique().tolist())
        sel_sources = st.multiselect("წყარო", options=sources, default=sources)

    with fc2:
        remote_filter = st.selectbox("ტიპი", ["ყველა", "მხოლოდ რემოუტ", "მხოლოდ ადგილობრივი"])

    with fc3:
        search_text = st.text_input("🔍 ძებნა სათაურში/კომპანიაში", "")

    filtered = df[df["source"].isin(sel_sources)].copy()

    if remote_filter == "მხოლოდ რემოუტ":
        filtered = filtered[filtered["remote"] == True]
    elif remote_filter == "მხოლოდ ადგილობრივი":
        filtered = filtered[filtered["remote"] == False]

    if search_text:
        mask = (
            filtered["title"].str.contains(search_text, case=False, na=False) |
            filtered["company"].str.contains(search_text, case=False, na=False) |
            filtered["location"].str.contains(search_text, case=False, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"ნაჩვენებია: **{len(filtered)}** / {len(df)}")

    # --- ცხრილი ---
    st.subheader("📋 შედეგები")

    _EN_TO_KA = {
        "source": "წყარო", "title": "სათაური", "company": "კომპანია",
        "location": "ლოკაცია", "posted": "გამოქვეყნდა", "geo_status": "🌍 სტატუსი",
        "salary": "💰 ხელფასი", "url": "ლინკი",
    }
    cols = [c for c in ("source", "title", "company", "location", "posted",
                        "salary", "geo_status", "url")
            if c in filtered.columns]
    display_df = filtered[cols].copy()
    display_df.columns = [_EN_TO_KA[c] for c in cols]
    col_config = {
        "ლინკი": st.column_config.LinkColumn("გახსნა", display_text="🔗"),
        "სათაური": st.column_config.TextColumn("სათაური", width="large"),
        "კომპანია": st.column_config.TextColumn("კომპანია", width="medium"),
        "წყარო": st.column_config.TextColumn("წყარო", width="small"),
        "🌍 სტატუსი": st.column_config.TextColumn("🌍 სტატუსი", width="medium"),
    }

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
    )

    # --- ჩამოტვირთვა ---
    st.divider()
    st.subheader("💾 ჩამოტვირთვა")
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 CSV ჩამოტვირთვა",
        data=csv,
        file_name=f"jobradar_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

    with st.expander("📊 სტატისტიკა წყაროების მიხედვით"):
        st.bar_chart(filtered["source"].value_counts())

else:
    st.info(
        "👈 **მარცხნივ:**\n\n"
        "1. **🌐 სად ვეძებთ** — საიტები\n"
        "2. **🔍 რა ვეძებთ** — ჩაწერე ტერმინი ➕\n"
        "3. **🌍 გეო-ფილტრი** — მხოლოდ საქართველოდან\n"
        "4. **🚀 ძებნა**\n\n"
        "**ტერმინები ინახება — refresh-ის შემდეგ დარჩება.**"
    )