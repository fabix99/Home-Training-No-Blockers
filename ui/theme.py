"""
Theme for Home Training Tracker – matches analytics dashboard layout.
"""
import streamlit as st

# Same DASHBOARD_CSS as volleyball analytics – No Blockers branding
DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700;800;900&display=swap');

.stApp { background: #FAFAFA; background-attachment: fixed; }

.main .block-container {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(250, 250, 255, 0.98) 100%);
    border-radius: 16px;
    padding: 3rem 2rem;
    box-shadow: 0 20px 60px rgba(5, 13, 118, 0.3), inset 0 0 100px rgba(5, 13, 118, 0.05);
    border: 2px solid rgba(5, 13, 118, 0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}

.main-header {
    text-align: left;
    margin-bottom: 0;
    font-family: 'Poppins', sans-serif;
    line-height: 1.1;
    padding: 0;
}

.main-header .brand-name {
    display: block;
    font-size: 4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #050d76 0%, #050d76 50%, #dbe7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -2px;
    margin-bottom: 0.2rem;
    animation: headerGlow 3s ease-in-out infinite;
}

.main-header .subtitle {
    display: block;
    font-size: 1.8rem;
    font-weight: 600;
    background: linear-gradient(135deg, #050d76 0%, #050d76 80%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 1px;
    margin-top: 0;
    opacity: 0.9;
}

.tagline-header {
    text-align: right;
    font-size: 1rem;
    font-weight: 600;
    color: #050d76;
    font-family: 'Poppins', sans-serif;
    letter-spacing: 3px;
    text-transform: uppercase;
    line-height: 1.6;
    opacity: 0.85;
    padding-top: 1rem;
}

@keyframes headerGlow {
    0%, 100% { filter: brightness(1); }
    50% { filter: brightness(1.15); }
}

/* Sidebar - Blue theme */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(5, 13, 118, 0.95) 0%, rgba(5, 13, 118, 0.95) 100%);
    backdrop-filter: blur(20px);
    border-right: 2px solid rgba(5, 13, 118, 0.5);
}

section[data-testid="stSidebar"] .stMarkdown h1 {
    color: #FFFFFF;
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #FFFFFF;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.3);
}

section[data-testid="stSidebar"] .stImage caption {
    color: #FFFFFF;
    font-weight: 500;
}

section[data-testid="stSidebar"] div[data-testid="stImage"] {
    text-align: center !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #FFFFFF !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
}

section[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: #FFFFFF !important;
    color: #050d76 !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    border-radius: 8px !important;
}

/* Top header bar */
header[data-testid="stHeader"],
section[data-testid="stHeader"] {
    background: #050d76 !important;
}

header[data-testid="stHeader"] button,
header[data-testid="stHeader"] a,
header[data-testid="stHeader"] div,
header[data-testid="stHeader"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Calendar grid - No Blockers theme (2 columns: name | week) */

/* Header: "Player" cell */
.calendar-header-cell {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    text-align: center;
    padding: 1rem 0.5rem !important;
    border-radius: 12px;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: linear-gradient(135deg, #050d76 0%, #050d76 100%) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.calendar-header-player {
    text-align: left;
    padding-left: 1rem !important;
}
.calendar-header-day.today {
    box-shadow: inset 0 0 0 2px rgba(255,255,255,0.3);
    font-weight: 800;
}

/* Header: 7 day headers in one row (same container) */
.calendar-header-days {
    display: flex !important;
    gap: 0.25rem;
    min-height: 52px;
    align-items: stretch !important;
}
.calendar-header-days .calendar-header-cell {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.15rem !important;
}
.calendar-header-day-main {
    display: block;
    line-height: 1.2;
}
.calendar-header-day-subtitle {
    display: block;
    font-size: 0.65em !important;
    font-weight: 500 !important;
    opacity: 0.9;
    line-height: 1.2;
    text-transform: none;
    letter-spacing: 0.02em;
}

/* Row containers: name column and week column same height */
section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:has(.player-name)) {
    align-items: stretch !important;
}
section.main div[data-testid="column"]:has(.player-name),
section.main div[data-testid="column"]:has(.calendar-row) {
    align-self: stretch !important;
}
/* Week column: inner wrappers fill height so .calendar-row can stretch */
section.main div[data-testid="column"]:has(.calendar-row) > div,
section.main div[data-testid="column"]:has(.calendar-row) > div > div {
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}
section.main div[data-testid="column"]:has(.calendar-row) .calendar-row {
    flex: 1 !important;
}

/* Cell marker: zero-size, for today/completed styling only */
.cell-marker {
    height: 0; min-height: 0; padding: 0; margin: 0;
    overflow: hidden; border: none; display: block;
}

/* Week row: 7 cells in one container, same height by construction */
.calendar-row {
    display: flex !important;
    gap: 0.25rem !important;
    min-height: 52px !important;
    align-items: stretch !important;
}
.calendar-row .calendar-cell {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 32px;
    padding: 1rem 0.3rem !important;
    background: linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(248,250,255,0.9) 100%) !important;
    border-radius: 12px;
    border: 1px solid rgba(5, 13, 118, 0.2) !important;
    box-shadow: 0 2px 12px rgba(5, 13, 118, 0.06) !important;
}
.calendar-row .calendar-cell:has(.cell-marker.today) {
    border-color: rgba(5, 13, 118, 0.4) !important;
    background: linear-gradient(145deg, rgba(219, 231, 255, 0.5) 0%, rgba(219, 231, 255, 0.2) 100%) !important;
}
.calendar-row .calendar-cell:has(.cell-marker.completed) {
    border-color: rgba(6, 167, 125, 0.4) !important;
    background: linear-gradient(145deg, rgba(6, 167, 125, 0.15) 0%, rgba(6, 167, 125, 0.05) 100%) !important;
}

/* Link as checkbox: centered, looks like the old checkbox */
.cell-checkbox {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    color: #050d76 !important;
    flex-shrink: 0;
}
.cell-checkbox-box {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 26px !important;
    min-height: 26px !important;
    border-radius: 5px !important;
    border: 2px solid rgba(5, 13, 118, 0.28) !important;
    background: rgba(255,255,255,0.9) !important;
    font-size: 0.875rem !important;
    font-weight: 700 !important;
}
.cell-checkbox:hover .cell-checkbox-box {
    border-color: rgba(5, 13, 118, 0.5) !important;
    background: rgba(219, 231, 255, 0.3) !important;
}
.cell-checkbox.checked .cell-checkbox-box {
    background: rgba(6, 167, 125, 0.15) !important;
    border-color: rgba(6, 167, 125, 0.5) !important;
    color: #06A77D !important;
}

.player-name {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    color: #2C3E50;
    padding: 1rem 1.25rem !important;
    background: linear-gradient(145deg, rgba(255,255,255,0.95) 0%, rgba(248,250,255,0.9) 100%) !important;
    border-radius: 12px;
    border: 1px solid rgba(5, 13, 118, 0.15);
    box-shadow: 0 2px 12px rgba(5, 13, 118, 0.06);
}

/* Main area buttons */
section.main .stButton > button {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: 2px solid rgba(5, 13, 118, 0.28) !important;
    background: #FFFFFF !important;
    color: #050d76 !important;
}

section.main .stButton > button:hover {
    background: rgba(5, 13, 118, 0.1) !important;
    border-color: #050d76 !important;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem;
    background: linear-gradient(145deg, rgba(255,255,255,0.6) 0%, rgba(5, 13, 118, 0.08) 100%);
    border: 2px dashed rgba(5, 13, 118, 0.3);
    border-radius: 16px;
    color: #2C3E50;
}

.empty-state .empty-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: #050d76;
    margin-bottom: 0.5rem;
}

.save-feedback {
    font-size: 0.875rem;
    font-weight: 700;
    color: #06A77D;
}

/* Workout 1, 2, 3 buttons: full width – target the 3-column row (only one with exactly 3 columns) */
section.main [data-testid="stHorizontalBlock"]:has(> div:first-child:nth-last-child(3)) {
    width: 100% !important;
}
section.main [data-testid="stHorizontalBlock"]:has(> div:first-child:nth-last-child(3)) > div {
    flex: 1 !important;
    min-width: 0 !important;
}
section.main [data-testid="stHorizontalBlock"]:has(> div:first-child:nth-last-child(3)) [data-testid="stPopover"] {
    width: 100% !important;
    display: block !important;
}
section.main [data-testid="stHorizontalBlock"]:has(> div:first-child:nth-last-child(3)) [data-testid="stPopover"] button {
    width: 100% !important;
}

section.main h1:first-of-type { display: none !important; }

.stMarkdown, .stApp { color: #2C3E50; font-family: 'Inter', sans-serif; }
</style>
"""


def apply_dashboard_theme() -> None:
    """Apply the No Blockers dashboard theme (matches analytics layout)."""
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
