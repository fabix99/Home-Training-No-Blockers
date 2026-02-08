"""
Home Training Tracker – Streamlit app.
Calendar view: one row per player, one week (7 days) per row. Toggle completion via links.
Workouts 1–3 at top; data from GitHub or local data/.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Union
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Ensure project root is on path so "ui" resolves when this module is loaded (e.g. Streamlit Cloud)
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
        return {} if ("completions" in path or "workouts" in path or "tokens" in path) else []


def read_text_from_github(repo, path: str) -> Optional[str]:
    """Read a text file from the repo. Returns content as string or None."""
    try:
        f = repo.get_contents(path)
        return f.decoded_content.decode().strip()
    except Exception:
        return None


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


USEFUL_INFO_DOC_URL = "https://drive.google.com/drive/folders/1pK5m9qT5TCKhbp2R7WeH0_nWArWyniCv"

# Workout of the week: fetched from this Google Doc. HTML export preserves links; we fall back to TXT.
WORKOUT_DOC_ID = "17zFCgNEfgNndKi19xvXNbk7ebg2HrV3DYUOV282aZ64"
WORKOUT_DOC_EXPORT_HTML = f"https://docs.google.com/document/d/{WORKOUT_DOC_ID}/export?format=html"
WORKOUT_DOC_EXPORT_URL = f"https://docs.google.com/document/d/{WORKOUT_DOC_ID}/export?format=txt"

# Cache TTL for fetched workout content (seconds)
WORKOUT_FETCH_CACHE_TTL = 300


def get_useful_info_doc_url() -> str:
    """Return Google Drive folder URL for Useful Information."""
    return USEFUL_INFO_DOC_URL


def _parse_workout_of_the_week_section(text: str) -> str:
    """Extract content under 'Workout of the week' until 'Exercise Pool' or 'End of List' (or end). Case-insensitive."""
    if not text or not text.strip():
        return ""
    start_marker = "workout of the week"
    end_markers = ("exercise pool", "end of list")
    lower = text.lower()
    start_idx = lower.find(start_marker)
    if start_idx == -1:
        return ""
    # Skip past the heading line so we don't repeat it
    line_end = text.find("\n", start_idx)
    if line_end == -1:
        content_start = start_idx + len(start_marker)
        rest = text[content_start:].strip()
    else:
        content_start = line_end + 1
        rest = text[content_start:].strip()
    rest_lower = rest.lower()
    end_idx = -1
    for marker in end_markers:
        idx = rest_lower.find(marker)
        if idx != -1 and (end_idx == -1 or idx < end_idx):
            end_idx = idx
    if end_idx != -1:
        rest = rest[:end_idx].strip()
    return rest.strip()


def _html_links_to_markdown(html_str: str) -> str:
    """Convert <a href="url">text</a> to [text](url); strip other tags; normalize whitespace."""
    # Convert <a href="...">...</a> or <a href='...'>...</a> to [text](url); inner text may contain tags
    def replace_a(match: re.Match) -> str:
        url = match.group(1).strip().replace("&amp;", "&")
        inner = match.group(2)
        text = re.sub(r"<[^>]+>", "", inner)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").strip()
        return f"[{text}]({url})" if text else f"[{url}]({url})"

    for pattern in (r'<a\s+href="([^"]+)"[^>]*>([\s\S]*?)</a>', r"<a\s+href='([^']+)'[^>]*>([\s\S]*?)</a>"):
        html_str = re.sub(pattern, replace_a, html_str, flags=re.IGNORECASE)
    # Strip remaining tags; replace block elements with newlines
    html_str = re.sub(r"</(?:p|div|br|tr|li)\s*>", "\n", html_str, flags=re.IGNORECASE)
    html_str = re.sub(r"<br\s*/?>", "\n", html_str, flags=re.IGNORECASE)
    html_str = re.sub(r"<[^>]+>", "", html_str)
    html_str = re.sub(r"\n{3,}", "\n\n", html_str)
    return html_str.strip()


def _parse_workout_section_from_html(html_raw: str) -> Optional[str]:
    """Extract 'Workout of the week' section from HTML and return markdown with links preserved."""
    if not html_raw or "workout of the week" not in html_raw.lower():
        return None
    # First convert links to markdown, then strip tags
    with_links = _html_links_to_markdown(html_raw)
    return _parse_workout_of_the_week_section(with_links)


def fetch_workout_of_the_week() -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch the Google Doc and return the "Workout of the week" section.
    Returns (content, error_message). On success content is non-empty and error is None; on failure content is None and error is set.
    Uses session-state cache with WORKOUT_FETCH_CACHE_TTL to avoid hitting Google on every rerun.
    """
    cache_key = "workout_of_the_week_cache"
    now = time.time()
    cached = st.session_state.get(cache_key)
    if cached is not None:
        ts, content, err = cached
        if now - ts < WORKOUT_FETCH_CACHE_TTL and content is not None:
            return (content, None)
        if now - ts < WORKOUT_FETCH_CACHE_TTL and err is not None:
            return (None, err)
    content = None
    err_msg = None
    try:
        # Try HTML first so links (e.g. Physitrack, YouTube) are preserved; TXT export strips URLs.
        for export_url, is_html in [(WORKOUT_DOC_EXPORT_HTML, True), (WORKOUT_DOC_EXPORT_URL, False)]:
            try:
                req = Request(export_url, headers={"User-Agent": "HomeTrainingNoBlockers/1.0"})
                with urlopen(req, timeout=10) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                if is_html:
                    parsed = _parse_workout_section_from_html(raw)
                else:
                    parsed = _parse_workout_of_the_week_section(raw)
                if parsed:
                    content = parsed
                    break
            except (URLError, HTTPError, OSError):
                continue
        if not content:
            err_msg = "Could not find 'Workout of the week' section in the document."
    except (URLError, HTTPError, OSError) as e:
        err_msg = f"Could not load workout: {e}"
    st.session_state[cache_key] = (now, content, err_msg)
    if err_msg and content is None:
        return (None, err_msg)
    return (content or "", None)


def _linkify(text: str) -> str:
    """Turn raw URLs in text into markdown links so they render clickable."""
    if not text:
        return text

    def replace_url(match: re.Match) -> str:
        url = match.group(0).rstrip(".,;:)'\"]")
        return f"[{url}]({url})"

    return re.sub(r"https?://\S+", replace_url, text)


# YouTube: match watch?v=ID or youtu.be/ID; capture full URL for extraction.
_YOUTUBE_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]{11})(?:[^\s]*)?",
    re.IGNORECASE,
)


def _extract_youtube_urls(text: str) -> List[str]:
    """Return list of canonical YouTube watch URLs (https://www.youtube.com/watch?v=ID) found in text."""
    urls = []
    for m in _YOUTUBE_URL_PATTERN.finditer(text):
        video_id = m.group(1)
        urls.append(f"https://www.youtube.com/watch?v={video_id}")
    return urls


def _is_youtube_only_line(s: str) -> bool:
    """True if the line is only a YouTube URL (possibly with surrounding whitespace)."""
    s = s.strip()
    if not s:
        return False
    m = _YOUTUBE_URL_PATTERN.match(s)
    return m is not None and m.end() == len(s)


def render_workout_content(content: str) -> None:
    """
    Render workout text: make links clickable, and embed YouTube videos in-place
    so they are playable on mobile without leaving the app.
    """
    if not content:
        return
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            st.markdown("")
            continue
        # Embed any YouTube URLs found in this line (works for "Video: https://..." or a lone URL)
        youtube_urls = _extract_youtube_urls(stripped)
        seen = set()
        for url in youtube_urls:
            if url not in seen:
                seen.add(url)
                st.markdown(f"[▶ {url}]({url})")
                st.video(url)
        # If the whole line was just a YouTube URL, we already embedded it; skip duplicate link
        if _is_youtube_only_line(stripped) and youtube_urls:
            continue
        # Show the line: if it already has markdown links (from HTML export), don't linkify
        if "](http" in line or "](https" in line:
            st.markdown(line)
        else:
            st.markdown(_linkify(line))


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


def _token_from_url(url: str) -> Optional[str]:
    """Extract ?token= value from a full URL."""
    if not url or "?" not in url:
        return None
    qs = parse_qs(urlparse(url).query)
    vals = qs.get("token", [None])
    return (vals[0] or "").strip() or None


def _parse_tokens_json(data: Union[dict, list]) -> Tuple[dict, Optional[str]]:
    """Parse combined tokens.json: return (token_to_player, full_view_token)."""
    if not isinstance(data, dict):
        return ({}, None)
    full_view_url = data.get("full_view_url") or ""
    players = data.get("players") or {}
    full_view_token = _token_from_url(full_view_url)
    token_to_player = {}
    for name, url in players.items():
        t = _token_from_url(url)
        if t:
            token_to_player[t] = name
    return (token_to_player, full_view_token)


_tokens_cache: Optional[Tuple[dict, Optional[str]]] = None


def _load_old_tokens() -> Tuple[dict, Optional[str]]:
    """Load old player_tokens.json + full_view_token.txt; return (token_to_player, full_view_token)."""
    token_to_player = _load_data("data/player_tokens.json", "player_tokens.json", {})
    if not isinstance(token_to_player, dict):
        return ({}, None)
    repo = get_github_repo()
    full_view_token = None
    if repo:
        full_view_token = read_text_from_github(repo, "data/full_view_token.txt")
    if not full_view_token:
        path = DATA_DIR / "full_view_token.txt"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                full_view_token = f.read().strip() or None
    return (token_to_player, full_view_token)


def _load_tokens_data() -> Tuple[dict, Optional[str]]:
    """Load data/tokens.json once and return (token_to_player, full_view_token). Fall back to old files if missing."""
    global _tokens_cache
    if _tokens_cache is not None:
        return _tokens_cache
    raw = _load_data("data/tokens.json", "tokens.json", {})
    _tokens_cache = _parse_tokens_json(raw)
    if not _tokens_cache[0] and not _tokens_cache[1]:
        _tokens_cache = _load_old_tokens()
    return _tokens_cache


def load_player_tokens() -> dict:
    """Load mapping { token: player_name } from combined data/tokens.json (full URLs)."""
    return _load_tokens_data()[0]


def load_full_view_token() -> Optional[str]:
    """Load the full-view token from combined data/tokens.json (full_view_url)."""
    return _load_tokens_data()[1]


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
        ("player_tokens", load_player_tokens),
        ("full_view_token", load_full_view_token),
        ("save_feedback_until", 0),
        ("save_error", None),
        ("player_locked_by_token", False),
        ("full_view_by_token", False),
        ("player_url_token", None),
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


def count_player_week_completions(week_start: date, player: str) -> int:
    """Number of days this player completed in the week."""
    comp = st.session_state.completions
    days = get_week_days(week_start)
    return sum(1 for d in days if player in comp.get(d.isoformat(), []))


def get_star_of_the_week(week_start: date) -> Optional[Tuple[List[str], int]]:
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


def get_participation_per_day(week_start: date) -> List[float]:
    """Participation % per day (0–100). Index 0 = Mon, ..., 6 = Sun."""
    players = st.session_state.players or []
    n = len(players)
    if n == 0:
        return [0.0] * 7
    comp = st.session_state.completions
    days = get_week_days(week_start)
    return [(100.0 * len(comp.get(d.isoformat(), [])) / n) for d in days]


def get_participation_per_player(week_start: date) -> dict:
    """Participation % per player for the week (0–100). Key = player name."""
    players = st.session_state.players or []
    if not players:
        return {}
    days = get_week_days(week_start)
    comp = st.session_state.completions
    result = {}
    for player in players:
        count = sum(1 for d in days if player in comp.get(d.isoformat(), []))
        result[player] = (100.0 * count / 7) if count else 0.0
    return result


def get_participation_overall(week_start: date) -> float:
    """Overall team participation % for the week (0–100)."""
    players = st.session_state.players or []
    if not players:
        return 0.0
    total_slots = len(players) * 7
    total = count_week_completions(week_start)
    return (100.0 * total / total_slots) if total_slots else 0.0


def render_participation_stats(week_start: date):
    """Render participation %: per day, per player (overview) or current player, and overall team."""
    players = st.session_state.players
    if not players:
        return
    days = get_week_days(week_start)
    today = date.today()
    per_day = get_participation_per_day(week_start)
    per_player = get_participation_per_player(week_start)
    overall = get_participation_overall(week_start)
    show_all = st.session_state.get("full_view_by_token")

    st.markdown("---")
    st.subheader("📈 Participation this week")

    # 1) Per day: one metric per day
    st.markdown("**By day** (share of players who logged that day)")
    day_cols = st.columns(7)
    for i, (d, pct) in enumerate(zip(days, per_day)):
        with day_cols[i]:
            label = d.strftime("%a")
            if d == today:
                label += " (today)"
            st.metric(label, f"{pct:.0f}%", None)
    st.markdown("")

    # 2) Per player: all players in overview, or just current player
    if show_all:
        st.markdown("**By player** (share of days logged this week)")
        with st.expander("See participation per player", expanded=True):
            n_cols = 6
            for start in range(0, len(players), n_cols):
                row_players = players[start : start + n_cols]
                row_cols = st.columns(len(row_players))
                for col, player in zip(row_cols, row_players):
                    with col:
                        pct = per_player.get(player, 0.0)
                        st.metric(player, f"{pct:.0f}%", None)
    else:
        p = st.session_state.selected_player
        pct = per_player.get(p, 0.0)
        st.markdown(f"**Your week:** {pct:.0f}% ({count_player_week_completions(week_start, p)}/7 days)")
    st.markdown("")

    # 3) Overall team
    st.markdown("**Team overall** (all days, all players)")
    st.metric("Participation", f"{overall:.0f}%", None)


def render_empty_players():
    """Phase 4: Empty state when no players."""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-title">No players yet</div>
        <div class="empty-body">Add player names to <code>data/players.json</code> (or in GitHub) to start tracking. One name per line in the list.</div>
    </div>
    """, unsafe_allow_html=True)


def _day_header_subtitle(d: date) -> Optional[str]:
    """Subtitle for day header: (NB Training) on Mon/Thu, (NB Match) on Fri."""
    w = d.weekday()  # 0=Mon, 3=Thu, 4=Fri
    if w in (0, 3):
        return "(NB Training)"
    if w == 4:
        return "(NB Match)"
    return None


def _ensure_selected_player():
    """Resolve ?token=: full-view token shows everyone; player token locks to that player; no/invalid token = no access."""
    players = st.session_state.players or []
    if not players:
        return
    token = st.query_params.get("token")
    full_view = st.session_state.get("full_view_token")
    token_to_player = st.session_state.get("player_tokens") or {}

    if token and full_view and token == full_view:
        st.session_state.full_view_by_token = True
        st.session_state.player_locked_by_token = False
        st.session_state.player_url_token = token
        url_player = st.query_params.get("player")
        if url_player and url_player in players:
            st.session_state.selected_player = url_player
        elif "selected_player" not in st.session_state or st.session_state.selected_player not in players:
            st.session_state.selected_player = players[0]
        return
    if token and token in token_to_player:
        player = token_to_player[token]
        if player in players:
            st.session_state.selected_player = player
            st.session_state.player_locked_by_token = True
            st.session_state.full_view_by_token = False
            st.session_state.player_url_token = token
            return
        st.session_state.player_locked_by_token = False
        st.session_state.player_url_token = None
    else:
        if token:
            st.session_state.player_locked_by_token = False
            st.session_state.player_url_token = None
        st.session_state.full_view_by_token = False
    url_player = st.query_params.get("player")
    if url_player and url_player in players:
        st.session_state.selected_player = url_player
    elif "selected_player" not in st.session_state or st.session_state.selected_player not in players:
        st.session_state.selected_player = players[0]


def render_player_selector():
    """Player dropdown – or read-only label when opened via private link (?token=). Overview (full-view) shows all players, no dropdown."""
    players = st.session_state.players
    if not players:
        render_empty_players()
        return
    _ensure_selected_player()
    if st.session_state.get("full_view_by_token"):
        st.markdown("**Overview – all players**")
        return
    if st.session_state.get("player_locked_by_token"):
        st.markdown(f"**Logged in as:** {st.session_state.selected_player}")
        return
    st.session_state.selected_player = st.selectbox(
        "Select your name",
        players,
        index=players.index(st.session_state.selected_player),
        key="calendar_selected_player",
    )


def _day_header_html(d: date, today: date) -> str:
    """Single day header HTML (for reuse in single-row and overview)."""
    sub = _day_header_subtitle(d)
    sub_html = f'<span class="calendar-header-day-subtitle">{sub}</span>' if sub else ''
    cls = "calendar-header-cell calendar-header-day" + (" today" if d == today else "")
    return (
        f'<div class="{cls}">'
        f'<span class="calendar-header-day-main">{d.strftime("%a")} {d.day}</span>'
        f'{sub_html}'
        f'</div>'
    )


def _player_day_cells(player: str, days: list, today: date) -> str:
    """HTML for one player's 7 day cells (links to toggle completion)."""
    token_suffix = f"&token={quote(st.session_state.player_url_token)}" if st.session_state.get("player_url_token") else ""
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
            f'<a href="?toggle={toggle_param}&player={quote(player)}{token_suffix}" target="_self" class="{check_class}" role="checkbox" aria-checked="{aria_checked}" title="Toggle completion">'
            f'<span class="cell-checkbox-box">{"✓" if is_done else ""}</span></a>'
            f'</div>'
        )
    return "".join(cells)


def render_calendar_grid(week_start: date, today: date):
    """Day headers + one row per player (overview) or selected player's row only. Call after render_player_selector and week switcher."""
    players = st.session_state.players
    if not players:
        return
    _ensure_selected_player()
    days = get_week_days(week_start)
    show_all = st.session_state.get("full_view_by_token")

    cal_col, = st.columns([1])
    with cal_col:
        if show_all:
            # Overview: header row = "Player" + 7 days; then one row per player
            day_headers = [_day_header_html(d, today) for d in days]
            header_row = (
                '<div class="calendar-header-row calendar-header-row-overview">'
                '<div class="calendar-header-cell calendar-header-player">Player</div>'
                f'<div class="calendar-header-days">{"".join(day_headers)}</div>'
                '</div>'
            )
            st.markdown(header_row, unsafe_allow_html=True)
            for player in players:
                cells_html = _player_day_cells(player, days, today)
                row_html = (
                    f'<div class="calendar-row calendar-row-overview">'
                    f'<div class="player-name">{player}</div>'
                    f'<div class="calendar-row-days">{cells_html}</div>'
                    '</div>'
                )
                st.markdown(row_html, unsafe_allow_html=True)
        else:
            # Single player: 7 day headers + one data row
            day_headers = [_day_header_html(d, today) for d in days]
            st.markdown(f'<div class="calendar-header-days">{"".join(day_headers)}</div>', unsafe_allow_html=True)
            player = st.session_state.selected_player
            cells_html = _player_day_cells(player, days, today)
            st.markdown(f'<div class="calendar-row">{cells_html}</div>', unsafe_allow_html=True)


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
        st.query_params["player"] = player
        if st.session_state.get("player_url_token"):
            st.query_params["token"] = st.session_state.player_url_token
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

    _ensure_selected_player()
    has_valid_token = (
        st.session_state.get("player_locked_by_token") or st.session_state.get("full_view_by_token")
    )
    if not has_valid_token:
        st.markdown("""
        <div class="main-header">
            <span class="brand-name">⚫ NO BLOCKERS</span>
            <span class="subtitle">Home Training Tracker</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**Welcome to the main page!**")
        st.markdown("To access your data, use the link that was shared individually with you. If you don't have it, ask Fabio, and save it for next time!")
        st.markdown("")
        st.markdown("But while you're here, here is the **workout of the week**:")
        workout_content, workout_error = fetch_workout_of_the_week()
        if workout_error:
            st.warning(workout_error)
            st.link_button("Open workout document", f"https://docs.google.com/document/d/{WORKOUT_DOC_ID}/edit", type="secondary")
        elif workout_content:
            render_workout_content(workout_content)
        return

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
            new_week = _monday_of_week(week_start - timedelta(days=7))
            st.session_state.week_start = new_week
            st.rerun()
    with col_next:
        if st.sidebar.button("Next →", use_container_width=True):
            new_week = _monday_of_week(week_start + timedelta(days=7))
            st.session_state.week_start = new_week
            st.rerun()

    # Sync date_input to current week before creating widget (avoids "cannot modify after instantiated")
    st.session_state["jump"] = week_start
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
        if st.session_state.get("player_locked_by_token"):
            p = st.session_state.selected_player
            my_count = count_player_week_completions(week_start, p)
            summary_text = f"Your progress: {my_count} day{'s' if my_count != 1 else ''} logged this week"
        else:
            week_count = count_week_completions(week_start)
            summary_text = f"This week: {week_count} workout{'s' if week_count != 1 else ''} logged"
            if week_count >= 7 * len(players):
                summary_text = "This week: everyone logged! 🏐"
    else:
        summary_text = "Add players to start"
    st.sidebar.caption(summary_text)

    if not st.session_state.get("player_locked_by_token"):
        star = get_star_of_the_week(week_start)
        if star:
            names, count = star
            label = "Stars of the week:" if len(names) > 1 else "Star of the week:"
            st.sidebar.caption(f"⭐ {label} {', '.join(names)} ({count})")

    st.sidebar.markdown("---")

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

    render_participation_stats(week_start)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Workout of the week – fetched from Google Doc
    workout_content, workout_error = fetch_workout_of_the_week()
    with st.popover("Workout of the week", use_container_width=True):
        if workout_error:
            st.warning(workout_error)
            st.link_button("Open workout document", f"https://docs.google.com/document/d/{WORKOUT_DOC_ID}/edit", type="secondary")
        elif workout_content:
            render_workout_content(workout_content)

    # 4. Useful Information
    st.link_button("📄 Useful Information", get_useful_info_doc_url(), type="secondary", use_container_width=True)

    # 5. Prev / Next week (at bottom)
    prev_week = _monday_of_week(week_start - timedelta(days=7))
    next_week = _monday_of_week(week_start + timedelta(days=7))
    sw_col1, sw_col2 = st.columns(2)
    with sw_col1:
        if st.button("← Prev week", key="prev_week", use_container_width=True):
            st.session_state.week_start = prev_week
            st.rerun()
    with sw_col2:
        if st.button("Next week →", key="next_week", use_container_width=True):
            st.session_state.week_start = next_week
            st.rerun()

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
