"""📚 ვაკანსიების ისტორია — ბაზიდან."""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Root საქაღალდის დამატება path-ში (import-ებისთვის)
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import connect, get_jobs, mark_applied, stats, toggle_favorite
from logging_utils import get_logger

log = get_logger("history")

st.set_page_config(page_title="ისტორია — JobRadar", page_icon="📚", layout="wide")

st.title("📚 ვაკანსიების ისტორია")
st.caption("ბაზაში შენახული ყველა ვაკანსია — გაფილტრე, მონიშნე, გადმოწერე")


# ─────────────────────────────────────────────
# ბაზასთან კავშირი
# ─────────────────────────────────────────────
conn = connect()
s = stats(conn)

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 სულ ბაზაში", s["total"] or 0)
c2.metric("🆕 ბოლო 24 სთ", s["last_24h"] or 0)
c3.metric("⭐ ფავორიტები", s["favorite"] or 0)
c4.metric("✅ მიმართული", s["applied"] or 0)

st.divider()

# ─────────────────────────────────────────────
# ფილტრები
# ─────────────────────────────────────────────
st.subheader("🔎 ფილტრები")

fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    period = st.selectbox(
        "📅 პერიოდი",
        ["ბოლო 24 სთ", "ბოლო 7 დღე", "ბოლო 30 დღე", "ყველა"],
        key="hist_period",
    )

with fc2:
    type_filter = st.selectbox(
        "📌 ტიპი",
        ["ყველა", "✅ მიმართული", "❌ არ მიმართული", "⭐ ფავორიტები"],
        key="hist_type",
    )

with fc3:
    sources_raw = conn.execute(
        "SELECT DISTINCT source FROM jobs ORDER BY source"
    ).fetchall()
    sources = ["ყველა"] + [r[0] for r in sources_raw]
    filter_source = st.selectbox("📡 წყარო", sources, key="hist_source")

with fc4:
    search_text = st.text_input(
        "🔍 ძებნა",
        placeholder="სათაური, კომპანია...",
        key="hist_search",
    )


# ─────────────────────────────────────────────
# მონაცემების წაკითხვა
# ─────────────────────────────────────────────
hours_map = {
    "ბოლო 24 სთ": 24,
    "ბოლო 7 დღე": 168,
    "ბოლო 30 დღე": 720,
    "ყველა": None,
}

only_applied = None
only_favorite = None

if type_filter == "✅ მიმართული":
    only_applied = 1
elif type_filter == "❌ არ მიმართული":
    only_applied = 0
elif type_filter == "⭐ ფავორიტები":
    only_favorite = 1

jobs = get_jobs(
    conn,
    only_new_hours=hours_map[period],
    only_applied=only_applied,
    only_favorite=only_favorite,
    source=None if filter_source == "ყველა" else filter_source,
    limit=2000,
)

# ტექსტური ძებნა
if search_text:
    q = search_text.lower()
    jobs = [
        j for j in jobs
        if q in (j["title"] or "").lower()
        or q in (j["company"] or "").lower()
        or q in (j["location"] or "").lower()
    ]

st.caption(f"ნაჩვენებია: **{len(jobs)}** ვაკანსია")


# ─────────────────────────────────────────────
# ინტერაქტიული ცხრილი
# ─────────────────────────────────────────────
if jobs:
    df = pd.DataFrame(jobs)
    df_display = df[
        ["fp", "score", "source", "title", "company", "location",
         "first_seen", "applied", "favorite", "url"]
    ].copy()

    df_display["applied"] = df_display["applied"].astype(bool)
    df_display["favorite"] = df_display["favorite"].astype(bool)

    edited = st.data_editor(
        df_display,
        column_config={
            "fp": None,  # დამალე
            "score": st.column_config.NumberColumn("⭐", width="small"),
            "source": st.column_config.TextColumn("წყარო", width="small"),
            "title": st.column_config.TextColumn("სათაური", width="large"),
            "company": st.column_config.TextColumn("კომპანია", width="medium"),
            "location": st.column_config.TextColumn("ლოკაცია", width="small"),
            "first_seen": st.column_config.TextColumn("პირველად", width="small"),
            "applied": st.column_config.CheckboxColumn("✅", width="small"),
            "favorite": st.column_config.CheckboxColumn("⭐", width="small"),
            "url": st.column_config.LinkColumn("გახსნა", display_text="🔗"),
        },
        disabled=[
            "score", "source", "title", "company",
            "location", "first_seen", "url",
        ],
        hide_index=True,
        use_container_width=True,
        key="history_editor",
    )

    # ცვლილებების შენახვა
    if st.button("💾 ცვლილებების შენახვა", type="primary"):
        changes = 0
        for i, row in edited.iterrows():
            orig = df_display.iloc[i]
            if bool(row["applied"]) != bool(orig["applied"]):
                mark_applied(conn, orig["fp"], bool(row["applied"]))
                changes += 1
            if bool(row["favorite"]) != bool(orig["favorite"]):
                toggle_favorite(conn, orig["fp"])
                changes += 1
        if changes:
            st.success(f"✅ შენახულია {changes} ცვლილება")
            st.rerun()
        else:
            st.info("ცვლილებები არ ყოფილა")

    # CSV ექსპორტი
    st.divider()
    st.subheader("💾 ჩამოტვირთვა")
    csv = df_display.drop(columns=["fp"]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 CSV ჩამოტვირთვა",
        data=csv,
        file_name=f"jobradar_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info(
        "ბაზა ცარიელია ან ფილტრს არაფერი ემთხვევა.\n\n"
        "გაუშვი `python cli.py` ან დაელოდე GitHub Actions-ს."
    )

conn.close()