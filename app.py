"""
Home Training Tracker – Streamlit app.
Calendar view: one row per player, one week (7 days) per row. Toggle completion via links.
Workouts 1–3 at top; data from GitHub or local data/.
"""

from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Union
from urllib.parse import quote

import streamlit as st

# -----------------------------------------------------------------------------
# Config & GitHub helpers
# -----------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"


def get_github_repo():
    """Return PyGitHub repo if token and repo name are set, else None."""
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("GITHUB_REPO")
    except Exception:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPO")
    if not token or not repo_name:
        return None
    from github import Github
    g = Github(token)
    return g.get_repo(repo_name)


def read_json_from_github(repo, path: str) -> Union[dict, list]:
    """Read a JSON file from the repo (e.g. 'data/players.json')."""
    try:
        f = repo.get_contents(path)
        return json.loads(f.decoded_content.decode())
    except Exception as e:
        st.warning(f"Could not read {path} from GitHub: {e}")
        return {} if "completions" in path or "workouts" in path else []


def write_json_to_github(repo, path: str, data: Union[dict, list], message: str) -> bool:
    """Overwrite a JSON file in the repo. Returns True on success."""
    try:
        content = json.dumps(data, indent=2)
        try:
            f = repo.get_contents(path)
            repo.update_file(path, message, content, f.sha)
        except Exception:
            repo.create_file(path, message, content)
        return True
    except Exception as e:
        st.error(f"Could not write to GitHub: {e}")
        return False


def read_local_json(name: str) -> Union[dict, list]:
    """Read JSON from local data/ directory."""
    path = DATA_DIR / name
    if not path.exists():
        return {} if name != "players.json" else []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_data(repo_path: str, local_name: str, default: Union[dict, list]) -> Union[dict, list]:
    """Load JSON from GitHub or local; return default if wrong type or missing."""
    repo = get_github_repo()
    if repo:
        data = read_json_from_github(repo, repo_path)
        return data if isinstance(data, type(default)) else default
    return read_local_json(local_name)


def load_players() -> list:
    """Load player list from GitHub or local."""
    return _load_data("data/players.json", "players.json", [])


def load_workouts() -> dict:
    """Load workouts from GitHub or local. Structure: week_start (YYYY-MM-DD) → { workout_1, workout_2, workout_3 }."""
    return _load_data("data/workouts.json", "workouts.json", {})


USEFUL_INFO_DOC_URL = "https://docs.google.com/document/d/1m-3EW-5I0-B03iaDi8KEFfrfxn30Bp0h/edit?usp=sharing"


def get_useful_info_doc_url() -> str:
    """Return Google Docs URL for Useful Information."""
    return USEFUL_INFO_DOC_URL


def get_workouts_for_week(workouts: dict, week_start: date) -> dict:
    """Get workout_1, workout_2, workout_3 for this week only. No fallback to legacy keys."""
    week_key = week_start.isoformat()
    week_data = workouts.get(week_key)
    if isinstance(week_data, dict) and "workout_1" in week_data:
        return week_data
    return {}


def save_workouts(workouts: dict) -> bool:
    """Persist workouts to GitHub (or local if no repo). Returns True on success."""
    repo = get_github_repo()
    if repo:
        return write_json_to_github(repo, "data/workouts.json", workouts, "Update workouts")
    path = DATA_DIR / "workouts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(workouts, f, indent=2)
    return True


def load_completions() -> dict:
    """Load completions { date: [player names] } from GitHub or local."""
    return _load_data("data/completions.json", "completions.json", {})


def save_completions(completions: dict) -> bool:
    """Persist completions to GitHub (or local if no repo). Returns True on success."""
    repo = get_github_repo()
    if repo:
        return write_json_to_github(repo, "data/completions.json", completions, "Update completions")
    path = DATA_DIR / "completions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(completions, f, indent=2)
    return True


# -----------------------------------------------------------------------------
# Session state & data loading
# -----------------------------------------------------------------------------

def init_session_state():
    """Set session state defaults (load data once, reset feedback/error)."""
    inits = [
        ("completions", load_completions),
        ("workouts", load_workouts),
        ("players", load_players),
        ("save_feedback_until", 0),
        ("save_error", None),
        ("is_editor", False),
    ]
    for key, val in inits:
        if key not in st.session_state:
            st.session_state[key] = val() if callable(val) else val


def completed(day: date, player: str) -> bool:
    key = day.isoformat()
    return player in st.session_state.completions.get(key, [])


def set_completed(day: date, player: str, value: bool):
    key = day.isoformat()
    if key not in st.session_state.completions:
        st.session_state.completions[key] = []
    lst = st.session_state.completions[key]
    if value and player not in lst:
        lst.append(player)
    elif not value and player in lst:
        lst.remove(player)


# Theme (matches analytics dashboard layout)
from ui.theme import apply_dashboard_theme


# -----------------------------------------------------------------------------
# Calendar UI (week view)
# -----------------------------------------------------------------------------

def get_week_days(week_start: date) -> list:
    """Return [Mon, Tue, ..., Sun] for the week starting at week_start (Monday)."""
    return [week_start + timedelta(days=i) for i in range(7)]


def count_week_completions(week_start: date) -> int:
    """Total number of (player, day) completions in this week."""
    comp = st.session_state.completions
    return sum(len(comp.get(d.isoformat(), [])) for d in get_week_days(week_start))


def get_star_of_the_week(week_start: date) -> tuple[list[str], int] | None:
    """Player(s) with the most completions this week. Returns (names, count) or None if no completions."""
    players = st.session_state.players or []
    if not players:
        return None
    comp = st.session_state.completions
    days = get_week_days(week_start)
    counts = [
        sum(1 for d in days if player in comp.get(d.isoformat(), []))
        for player in players
    ]
    if not counts or max(counts) == 0:
        return None
    max_count = max(counts)
    stars = [p for p, c in zip(players, counts) if c == max_count]
    return (stars, max_count)


def render_empty_players():
    """Phase 4: Empty state when no players."""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-title">No players yet</div>
        <div class="empty-body">Add player names to <code>data/players.json</code> (or in GitHub) to start tracking. One name per line in the list.</div>
    </div>
    """, unsafe_allow_html=True)


def _day_header_subtitle(d: date) -> str | None:
    """Subtitle for day header: (NB Training) on Mon/Thu, (NB Match) on Fri."""
    w = d.weekday()  # 0=Mon, 3=Thu, 4=Fri
    if w in (0, 3):
        return "(NB Training)"
    if w == 4:
        return "(NB Match)"
    return None


def _ensure_selected_player():
    """Initialize or validate selected player in session state."""
    players = st.session_state.players or []
    if not players:
        return
    if "selected_player" not in st.session_state or st.session_state.selected_player not in players:
        st.session_state.selected_player = players[0]


def render_player_selector():
    """Player dropdown – call first for user-friendly flow."""
    players = st.session_state.players
    if not players:
        render_empty_players()
        return
    _ensure_selected_player()
    st.session_state.selected_player = st.selectbox(
        "Select your name",
        players,
        index=players.index(st.session_state.selected_player),
        key="calendar_selected_player",
    )


def render_calendar_grid(week_start: date, today: date):
    """Day headers + selected player's row (7 cells). Call after render_player_selector and week switcher."""
    players = st.session_state.players
    if not players:
        return
    _ensure_selected_player()
    player = st.session_state.selected_player
    days = get_week_days(week_start)

    # Header row: 7 day headers; data row: 7 checkboxes (name only in dropdown above)
    # Wrapped in column for mobile scroll CSS
    cal_col, = st.columns([1])
    with cal_col:
        day_headers = []
        for d in days:
            sub = _day_header_subtitle(d)
            sub_html = f'<span class="calendar-header-day-subtitle">{sub}</span>' if sub else ''
            cls = "calendar-header-cell calendar-header-day" + (" today" if d == today else "")
            day_headers.append(
                f'<div class="{cls}">'
                f'<span class="calendar-header-day-main">{d.strftime("%a")} {d.day}</span>'
                f'{sub_html}'
                f'</div>'
            )
        st.markdown(f'<div class="calendar-header-days">{"".join(day_headers)}</div>', unsafe_allow_html=True)

        # Data row: 7 checkboxes
        cells = []
        for d in days:
            date_key = d.isoformat()
            is_today = d == today
            is_done = completed(d, player)
            cell_cls = "cell" + (" today" if is_today else "") + (" completed" if is_done else "")
            toggle_param = quote(f"{player}|{date_key}")
            check_class = "cell-checkbox checked" if is_done else "cell-checkbox"
            aria_checked = "true" if is_done else "false"
            cells.append(
                f'<div class="calendar-cell">'
                f'<div class="cell-marker {cell_cls}" aria-hidden="true"></div>'
                f'<a href="?toggle={toggle_param}" target="_self" class="{check_class}" role="checkbox" aria-checked="{aria_checked}" title="Toggle completion">'
                f'<span class="cell-checkbox-box">{"✓" if is_done else ""}</span></a>'
                f'</div>'
            )
        st.markdown(f'<div class="calendar-row">{"".join(cells)}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing d (ISO week: Mon–Sun)."""
    return d - timedelta(days=d.weekday())


def _handle_toggle_param():
    """If ?toggle=player|date is set, toggle that completion and rerun. Returns True if rerun requested."""
    toggle_val = st.query_params.get("toggle")
    if not toggle_val or "|" not in toggle_val:
        return
    try:
        player_part, date_str = toggle_val.split("|", 1)
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
        player = player_part
        if player in (st.session_state.players or []):
            cur = completed(day, player)
            set_completed(day, player, not cur)
            if save_completions(st.session_state.completions):
                st.session_state.save_feedback_until = time.time() + 2.0
                st.session_state.save_error = None
            else:
                st.session_state.save_error = "Could not save. Check connection or GitHub token."
        st.query_params["toggle"] = None
        st.rerun()
    except (ValueError, TypeError):
        st.query_params["toggle"] = None


def main():
    st.set_page_config(
        page_title="Home Training Tracker",
        page_icon="🏐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    apply_dashboard_theme()
    init_session_state()

    _handle_toggle_param()  # may rerun

    today = date.today()
    if "week_start" not in st.session_state:
        st.session_state.week_start = _monday_of_week(today)

    week_start = st.session_state.week_start
    week_end = week_start + timedelta(days=6)
    players = st.session_state.players

    # ---------- Sidebar (matches analytics: logo, team name, navigation) ----------
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
        key="jump"
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

    # Editor: unlock with password (EDITOR_PASSWORD in Secrets)
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
        pw = st.sidebar.text_input("Editor password", type="password", key="editor_pw")
        if st.sidebar.button("Unlock editing", use_container_width=True) and pw == editor_password:
            st.session_state.is_editor = True
            st.rerun()

    # ---------- Main header (matches analytics: NO BLOCKERS + subtitle | tagline) ----------
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
    players = st.session_state.players
    if not players:
        return

    # 2. Days of the week + checkboxes (calendar)
    render_calendar_grid(week_start, today)

    # 3. Workout 1, 2, 3 – content per week
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

    # 4. Useful Information
    st.link_button("📄 Useful Information", get_useful_info_doc_url(), type="secondary", use_container_width=True)

    # 5. Prev / Next week (at bottom)
    week_label = f"Week of {week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    sw_col1, sw_col2 = st.columns(2)
    with sw_col1:
        if st.button("← Prev week", key="prev_week", use_container_width=True):
            st.session_state.week_start = prev_week
            st.rerun()
    with sw_col2:
        if st.button("Next week →", key="next_week", use_container_width=True):
            st.session_state.week_start = next_week
            st.rerun()
    st.markdown(f"**{week_label}**")

    st.markdown("---")

    # Edit workouts (this week only) – visible when editor is unlocked
    if st.session_state.is_editor:
        st.subheader("✏️ Edit workouts (this week only)")
        week_workouts = get_workouts_for_week(st.session_state.workouts, week_start)
        w1_title = st.text_input("Workout 1 – Title", value=week_workouts.get("workout_1", {}).get("title", ""), key="ew1_title")
        w1_desc = st.text_area("Workout 1 – Description", value=week_workouts.get("workout_1", {}).get("description", ""), key="ew1_desc", height=120)
        w2_title = st.text_input("Workout 2 – Title", value=week_workouts.get("workout_2", {}).get("title", ""), key="ew2_title")
        w2_desc = st.text_area("Workout 2 – Description", value=week_workouts.get("workout_2", {}).get("description", ""), key="ew2_desc", height=120)
        w3_title = st.text_input("Workout 3 – Title", value=week_workouts.get("workout_3", {}).get("title", ""), key="ew3_title")
        w3_desc = st.text_area("Workout 3 – Description", value=week_workouts.get("workout_3", {}).get("description", ""), key="ew3_desc", height=120)
        if st.button("Save workouts for this week", type="primary", key="save_workouts_btn"):
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

    # Save feedback ("Saved" for 2s) or error + retry
    now = time.time()
    if st.session_state.save_feedback_until and now < st.session_state.save_feedback_until:
        st.markdown('<p class="save-feedback">✓ Saved</p>', unsafe_allow_html=True)
    if st.session_state.save_error:
        st.error(st.session_state.save_error)
        if st.button("Retry save", key="retry_save"):
            st.session_state.save_error = None
            if save_completions(st.session_state.completions):
                st.session_state.save_feedback_until = time.time() + 2.0
                st.rerun()
            else:
                st.session_state.save_error = "Still could not save."


if __name__ == "__main__":
    main()
