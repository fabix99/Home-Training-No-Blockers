"""
Home Training Tracker – mobile-friendly Streamlit entry point.
Same app as app.py but with initial_sidebar_state="auto" and responsive CSS for small screens.
Run with: streamlit run mobile-app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from app import (
    _handle_toggle_param,
    _monday_of_week,
    apply_dashboard_theme,
    count_week_completions,
    get_star_of_the_week,
    get_useful_info_doc_url,
    get_workouts_for_week,
    init_session_state,
    render_calendar_grid,
    render_player_selector,
    save_completions,
    save_workouts,
)
from datetime import date, timedelta
import time

# Mobile-only CSS: responsive overrides for viewports <= 768px
MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }
    .main-header .brand-name { font-size: 2rem !important; }
    .main-header .subtitle { font-size: 1.2rem !important; }
    .tagline-header {
        font-size: 0.8rem !important;
        letter-spacing: 1px !important;
        text-align: left !important;
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stImage"] img {
        max-width: 100px !important;
    }
    /* Week column: horizontal scroll so all 7 days are reachable */
    .calendar-header-days,
    .calendar-row {
        min-width: 320px !important;
    }
    .calendar-header-days .calendar-header-cell {
        min-width: 44px !important;
    }
    section.main div[data-testid="column"]:has(.calendar-header-days),
    section.main div[data-testid="column"]:has(.calendar-row) {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        position: relative !important;
        box-shadow: inset -16px 0 12px -8px rgba(250,250,250,0.95) !important;
    }
    /* Touch targets >= 44px for calendar cells and checkboxes */
    .calendar-row .calendar-cell {
        min-width: 44px !important;
        min-height: 44px !important;
        padding: 0.5rem 0.2rem !important;
    }
    .calendar-row .calendar-cell .cell-checkbox {
        min-width: 100% !important;
        min-height: 100% !important;
    }
    .cell-checkbox-box,
    .cell-checkbox {
        min-width: 44px !important;
        min-height: 44px !important;
    }
    section[data-testid="stSidebar"] .stButton > button,
    section.main .stButton > button {
        min-height: 44px !important;
    }
    .player-name { padding: 0.75rem 0.5rem !important; font-size: 1rem !important; }
    /* Empty state and errors: compact, no overflow */
    .empty-state {
        padding: 1.5rem !important;
        max-width: 100% !important;
        word-wrap: break-word !important;
    }
    .empty-state .empty-title { font-size: 1.2rem !important; }
    .empty-state .empty-body { font-size: 0.9rem !important; }
    section.main [data-testid="stAlert"] {
        max-width: 100% !important;
        word-wrap: break-word !important;
        padding: 0.75rem !important;
    }
    .save-feedback { font-size: 0.8rem !important; }
}
</style>
"""


def main():
    st.set_page_config(
        page_title="Home Training Tracker",
        page_icon="🏐",
        layout="wide",
        initial_sidebar_state="auto",
    )
    apply_dashboard_theme()
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    init_session_state()

    _handle_toggle_param()

    today = date.today()
    if "week_start" not in st.session_state:
        st.session_state.week_start = _monday_of_week(today)

    week_start = st.session_state.week_start
    week_end = week_start + timedelta(days=6)
    players = st.session_state.players

    logo_path = Path(__file__).parent / "static" / "logo.jpg"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=150, caption="No Blockers Team")
    st.sidebar.markdown("---")

    st.sidebar.title("📊 Navigation")
    st.sidebar.markdown("**Choose week:**")

    col_prev, col_next = st.sidebar.columns(2)
    with col_prev:
        if st.sidebar.button("← Prev", use_container_width=True):
            st.session_state.week_start = week_start - timedelta(days=7)
            st.rerun()
    with col_next:
        if st.sidebar.button("Next →", use_container_width=True):
            st.session_state.week_start = week_start + timedelta(days=7)
            st.rerun()

    jump_to = st.sidebar.date_input(
        "Jump to week",
        value=week_start,
        format="YYYY-MM-DD",
        key="jump_mobile",
    )
    if jump_to != week_start:
        st.session_state.week_start = _monday_of_week(jump_to)
        st.rerun()

    st.sidebar.markdown("---")
    if players:
        week_count = count_week_completions(week_start)
        summary_text = f"This week: {week_count} workout{'s' if week_count != 1 else ''} logged"
        if week_count >= 7 * len(players):
            summary_text = "This week: everyone logged! 🏐"
    else:
        summary_text = "Add players to start"
    st.sidebar.caption(summary_text)

    star = get_star_of_the_week(week_start)
    if star:
        names, count = star
        label = "Stars of the week:" if len(names) > 1 else "Star of the week:"
        st.sidebar.caption(f"⭐ {label} {', '.join(names)} ({count})")

    st.sidebar.markdown("---")
    editor_password = None
    try:
        editor_password = st.secrets.get("EDITOR_PASSWORD")
    except Exception:
        editor_password = os.environ.get("EDITOR_PASSWORD")
    if st.session_state.is_editor:
        if st.sidebar.button("🔒 Lock editing", use_container_width=True):
            st.session_state.is_editor = False
            st.rerun()
    elif editor_password:
        pw = st.sidebar.text_input("Editor password", type="password", key="editor_pw_mobile")
        if st.sidebar.button("Unlock editing", use_container_width=True) and pw == editor_password:
            st.session_state.is_editor = True
            st.rerun()

    col_header1, col_header2 = st.columns([3, 2])
    with col_header1:
        st.markdown("""
        <div class="main-header">
            <span class="brand-name">⚫ NO BLOCKERS</span>
            <span class="subtitle">Home Training Tracker</span>
        </div>
        """, unsafe_allow_html=True)
    with col_header2:
        st.markdown("""
        <div class="tagline-header">
            NO FEAR. NO LIMITS.<br>NO BLOCKERS.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Select your name
    render_player_selector()
    if not st.session_state.players:
        return

    # 2. Days of the week + checkboxes (calendar)
    st.caption("Swipe for all 7 days")
    render_calendar_grid(week_start, today)

    # 4. Workout 1, 2, 3
    week_workouts = get_workouts_for_week(st.session_state.workouts, week_start)
    w1, w2, w3 = st.columns(3)
    for col, (btn_label, workout_key) in enumerate(
        [("Workout 1", "workout_1"), ("Workout 2", "workout_2"), ("Workout 3", "workout_3")]
    ):
        with [w1, w2, w3][col]:
            workout = week_workouts.get(workout_key)
            with st.popover(btn_label, width="stretch"):
                if workout:
                    st.markdown(f"**{workout.get('title', 'Workout')}**")
                    st.markdown(workout.get("description", "").replace("\n", "\n\n"))
                else:
                    st.info("No workout defined.")

    # 5. Useful Information
    st.link_button("📄 Useful Information", get_useful_info_doc_url(), type="secondary", use_container_width=True)

    # 6. Prev / Next week (at bottom)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    sw_col1, sw_col2 = st.columns(2)
    with sw_col1:
        if st.button("← Prev week", key="mobile_prev_week", use_container_width=True):
            st.session_state.week_start = prev_week
            st.rerun()
    with sw_col2:
        if st.button("Next week →", key="mobile_next_week", use_container_width=True):
            st.session_state.week_start = next_week
            st.rerun()

    st.markdown("---")

    if st.session_state.is_editor:
        st.subheader("✏️ Edit workouts (this week only)")
        week_workouts = get_workouts_for_week(st.session_state.workouts, week_start)
        w1_title = st.text_input("Workout 1 – Title", value=week_workouts.get("workout_1", {}).get("title", ""), key="ew1_title_m")
        w1_desc = st.text_area("Workout 1 – Description", value=week_workouts.get("workout_1", {}).get("description", ""), key="ew1_desc_m", height=120)
        w2_title = st.text_input("Workout 2 – Title", value=week_workouts.get("workout_2", {}).get("title", ""), key="ew2_title_m")
        w2_desc = st.text_area("Workout 2 – Description", value=week_workouts.get("workout_2", {}).get("description", ""), key="ew2_desc_m", height=120)
        w3_title = st.text_input("Workout 3 – Title", value=week_workouts.get("workout_3", {}).get("title", ""), key="ew3_title_m")
        w3_desc = st.text_area("Workout 3 – Description", value=week_workouts.get("workout_3", {}).get("description", ""), key="ew3_desc_m", height=120)
        if st.button("Save workouts for this week", type="primary", key="save_workouts_btn_m"):
            workouts = dict(st.session_state.workouts)
            week_key = week_start.isoformat()
            workouts[week_key] = {
                "workout_1": {"title": w1_title or "Workout 1", "description": w1_desc or ""},
                "workout_2": {"title": w2_title or "Workout 2", "description": w2_desc or ""},
                "workout_3": {"title": w3_title or "Workout 3", "description": w3_desc or ""},
            }
            if save_workouts(workouts):
                st.session_state.workouts = workouts
                st.success("Workouts saved for this week.")
                st.rerun()
            else:
                st.error("Could not save. Check connection or GitHub token.")
        st.markdown("---")

    now = time.time()
    if st.session_state.save_feedback_until and now < st.session_state.save_feedback_until:
        st.markdown('<p class="save-feedback">✓ Saved</p>', unsafe_allow_html=True)
    if st.session_state.save_error:
        st.error("Couldn't save. Check connection or try again.")
        if st.button("Retry save", key="retry_save_m"):
            st.session_state.save_error = None
            if save_completions(st.session_state.completions):
                st.session_state.save_feedback_until = time.time() + 2.0
                st.rerun()
            else:
                st.session_state.save_error = "Still could not save."


if __name__ == "__main__":
    main()
