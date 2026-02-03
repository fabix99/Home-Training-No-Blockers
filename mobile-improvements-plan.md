# Mobile interface – suggestions and plan

Prioritized list of improvements for the mobile-friendly Home Training Tracker (`mobile-app.py`), with concrete steps.

---

## 1. Ensure all 7 days are visible or clearly scrollable (high)

**Problem:** On narrow viewports the week row can show only 5–6 cells; Mon–Sun should all be reachable.

**Suggestions:**
- Give the calendar “week” column a **horizontal scroll** with a visible cue (e.g. fade or “swipe” hint on the right).
- Set a **min-width** on the row so it doesn’t shrink below 7 tappable cells; the container scrolls instead.

**Plan:**
- In `mobile-app.py` (MOBILE_CSS): ensure the column that holds `.calendar-header-days` and `.calendar-row` has `overflow-x: auto`, `-webkit-overflow-scrolling: touch`, and a min-width (e.g. 320px or 7 × 44px). Optionally add a small “scroll for more days” label or right-edge gradient in CSS.
- **Files:** `mobile-app.py` (MOBILE_CSS block).  
- **Effort:** Small (CSS only).

---

## 2. Touch targets at least 44px (high – verify)

**Problem:** Buttons and day cells must be easy to tap; some elements might still be under 44px on small screens.

**Suggestions:**
- Audit all interactive elements (day cells, checkboxes, Workout 1/2/3, sidebar buttons).
- Enforce **min-height/min-width: 44px** (and padding) for tap areas in the mobile media query.

**Plan:**
- In MOBILE_CSS `@media (max-width: 768px)`: set `.calendar-row .calendar-cell`, `.cell-checkbox`, `.cell-checkbox-box`, and sidebar/main buttons to min 44px where needed. Use padding on the link/button rather than only the inner box so the full cell is tappable.
- **Files:** `mobile-app.py` (MOBILE_CSS).  
- **Effort:** Small (CSS only).

---

## 3. Hide or replace Streamlit “Deploy” header on mobile (medium)

**Problem:** The top bar shows “Deploy” and generic Streamlit controls, which can confuse users.

**Suggestions:**
- **Option A:** Use Streamlit config or custom CSS to hide the header in the mobile entry point (if acceptable for your deployment).
- **Option B:** Document that “Deploy” is a dev/Streamlit artifact and disappears when deployed to Streamlit Cloud or your own server.
- **Option C:** If you host the app, set a custom title/branding so the bar shows “Home Training” or “No Blockers” instead.

**Plan:**
- **Option A:** In `.streamlit/config.toml` (or a mobile-specific config if you add one), set `[browser]` / theme options; or in MOBILE_CSS add a rule to hide `header[data-testid="stHeader"]` on mobile (may require `!important`). Weigh against losing the sidebar toggle.
- **Option B:** Add one line to README or this plan: “The ‘Deploy’ label in the top bar is Streamlit’s default and is not shown in production.”
- **Option C:** When deploying, set `server.headless = true` and use Streamlit Cloud’s app title; no code change.
- **Files:** `mobile-app.py` or `.streamlit/config.toml`, README.  
- **Effort:** Small (config/docs or a few lines of CSS).

---

## 4. Scroll cue for horizontal calendar (medium)

**Problem:** Users may not realize they can scroll horizontally to see all 7 days.

**Suggestions:**
- Add a subtle **right-edge gradient** or “shadow” so it’s clear more content is to the right.
- Optionally add a short **text hint** above or below the first row (e.g. “Swipe for all days”) that can be dismissed or hidden after first scroll (latter would need JS or a session-state flag and conditional message in Python).

**Plan:**
- **CSS-only:** Wrap the scrollable calendar section in a container that has `position: relative` and a `::after` pseudo-element with a linear-gradient (transparent → light gray/blue) on the right edge, so the row “fades” at the end and suggests more content.
- **With copy:** In `mobile-app.py`, above the calendar block, add a single `st.caption("Swipe for all 7 days")` that is always shown on mobile (no JS). Keep it short so it doesn’t clutter the UI.
- **Files:** `mobile-app.py` (MOBILE_CSS + optional caption).  
- **Effort:** Small.

---

## 5. Reduce vertical length with many players (medium, later)

**Problem:** With many players, the list (name + 7 cells each) gets long and requires a lot of scrolling.

**Suggestions:**
- **Collapsed summary:** Show one line per player (name + “3/7” or “3 workouts”) with a tap/chevron to expand and show the 7-day row.
- **Sticky day headers:** When scrolling vertically, keep the “Mon, Tue, …” row sticky at the top so users always see which column is which (complex in Streamlit with custom HTML).
- **Lazy loading:** Only render the first N players and a “Load more” button (requires refactor of `render_week_calendar` and state).

**Plan:**
- **Phase 1:** Document the idea; no code change until the roster grows.
- **Phase 2:** If needed, add an “accordion” pattern: in `mobile-app.py` (or a shared component), render each player as an expander (e.g. `st.expander(player_name, expanded=False)` with the 7 cells inside). Default collapsed; user taps to open. Reduces initial scroll length.
- **Files:** `mobile-app.py`, possibly `app.py` if we add a shared “render_week_calendar_mobile_compact” and call it from `mobile-app.py` only.
- **Effort:** Medium (layout/state changes).

---

## 6. Sidebar behavior and navigation (low)

**Problem:** On mobile, the sidebar is collapsed by default; week navigation (Prev/Next, Jump to week) is behind the hamburger/drawer. Fine for v1, but we could make week switching more visible.

**Suggestions:**
- Add a **compact week switcher** in the main area on mobile only (e.g. “← Week of 2 Feb | Next →” or two buttons) so users can change the week without opening the sidebar.
- Keep the full sidebar for jump-to-date and editor password.

**Plan:**
- In `mobile-app.py`, inside the mobile layout block: add a row above the week label with two buttons “Prev week” and “Next week” that update `st.session_state.week_start` and rerun. Style with MOBILE_CSS so it’s full-width and touch-friendly. Keep sidebar as-is for jump and editor.
- **Files:** `mobile-app.py` (one small block of Streamlit code + optional CSS).  
- **Effort:** Small.

---

## 7. Empty state and errors (low)

**Problem:** Empty state (“No players yet”) and save-error messages should be clear and not overwhelming on small screens.

**Suggestions:**
- In MOBILE_CSS, reduce padding and font size for `.empty-state` and `.save-feedback` / error blocks on mobile (already partly done; verify and tighten).
- Ensure error messages wrap and don’t overflow; use short, actionable copy (“Couldn’t save. Check connection.”).

**Plan:**
- Review MOBILE_CSS for `.empty-state`, `st.error` container, and `.save-feedback`; set `max-width: 100%`, `word-wrap: break-word`, and comfortable padding. Optionally in `app.py` (or only in mobile-app if we duplicate messages) shorten the save-error string for mobile (e.g. via a flag or a helper that returns short vs long message). Prefer one message in the app and style it in CSS.
- **Files:** `mobile-app.py` (MOBILE_CSS).  
- **Effort:** Small.

---

## 8. PWA / “Add to Home Screen” (optional, later)

**Problem:** Users might want the app as an icon on their phone home screen for quick access.

**Suggestions:**
- Add a **web app manifest** (`manifest.json`) with name, short_name, icons, theme_color, display: standalone.
- Add a **meta viewport** and **theme-color** in the Streamlit custom component or via `st.markdown` + HTML in the main script (if supported).
- Document in README that the app can be “added to home screen” when deployed over HTTPS.

**Plan:**
- Create `static/manifest.json`; add a link in the app’s HTML (e.g. via `st.components.v1.html` or Streamlit’s static file serving + documentation). Configure icons (e.g. 192x192, 512x512). Verify with Streamlit Cloud / your host that HTTPS and manifest are served.
- **Files:** New `static/manifest.json`, README, possibly one HTML snippet in `mobile-app.py`.  
- **Effort:** Medium (icons + manifest + testing).

---

## Implementation order (summary)

| Priority | Item | Effort | When |
|----------|------|--------|------|
| 1 | All 7 days visible / scrollable | Small | Next |
| 2 | Touch targets 44px (verify) | Small | Next |
| 3 | “Deploy” header (hide or document) | Small | Soon |
| 4 | Scroll cue for calendar | Small | Soon |
| 5 | Compact list for many players | Medium | When roster grows |
| 6 | Week switcher in main area | Small | Optional |
| 7 | Empty state & errors on mobile | Small | Optional |
| 8 | PWA / Add to Home Screen | Medium | Later |

---

## Notes

- All changes for the mobile entry point should stay in `mobile-app.py` (and optionally shared helpers) so `app.py` and `ui/theme.py` remain unchanged.
- Test on real devices (iOS Safari, Android Chrome) after each change; DevTools device mode is a good first check.
- Breakpoint is `768px`; consider a tablet breakpoint at `1024px` later if needed.
