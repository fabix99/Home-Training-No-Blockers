# Home Training Tracker

Streamlit app for your volleyball club: calendar view where each player can mark at-home workouts and see the workout of the day. Data is stored in this repo (or locally when no GitHub token is set).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Mobile-friendly version:** Run `streamlit run mobile-app.py` for a layout tuned for small screens (sidebar collapsed by default, week switcher in main area, touch-friendly calendar). The "Deploy" label in the top bar is Streamlit’s default when running locally and is not shown when deployed to Streamlit Cloud.

- **Without GitHub:** The app reads and writes `data/players.json`, `data/workouts.json`, and `data/completions.json` from the `data/` folder. Edit those files to add players and workouts.
- **With GitHub:** Create `.streamlit/secrets.toml` (see below) so the app reads/writes the same files in the GitHub repo.

## GitHub setup (optional)

1. Push this repo to GitHub (e.g. `your-username/Home-Training-No-Blockers`).
2. Create a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope.
3. **Local:** Create `.streamlit/secrets.toml`:
   ```toml
   GITHUB_TOKEN = "ghp_xxxx..."
   GITHUB_REPO = "your-username/Home-Training-No-Blockers"
   ```
4. **Streamlit Cloud:** In the app dashboard, add `GITHUB_TOKEN` and `GITHUB_REPO` in Secrets.

The app will then load and save `data/players.json`, `data/workouts.json`, and `data/completions.json` from that repo.

## Before publishing on Streamlit Cloud

1. **Push the repo** – Code + `data/players.json`, `data/workouts.json` (and optionally `data/completions.json`) are in the repo.
2. **Create a token** – [GitHub → Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens). New token with **repo** scope (read/write repo contents).
3. **Add Secrets** – In Streamlit Cloud: your app → Settings → Secrets. Add:
   - `GITHUB_TOKEN` = `ghp_xxxx...` (the token)
   - `GITHUB_REPO` = `your-username/Home-Training-No-Blockers` (same repo you deployed from).
4. **Redeploy** – Save secrets and redeploy so the app picks them up.

After that, every checkbox toggle reads `data/completions.json` from the repo via the API, updates it, and writes it back. If the file doesn’t exist yet, the app creates it on first save.

## Data files

- **data/players.json** – Fixed list of player names (one row per player in the calendar).
- **data/workouts.json** – Workouts per week (used by the Begum/Fabio editor only). The **Workout of the week** shown in the app is fetched from a Google Doc (see below).
- **data/completions.json** – Who completed which day (`YYYY-MM-DD` → list of player names). Updated when someone checks the box.

Edit `players.json` in the repo (or in `data/`).

## Workout of the week (Google Doc)

The app shows a single **Workout of the week** button. The content is fetched automatically from a Google Doc: the section between **"Workout of the week"** and **"Exercise Pool"** is displayed. The doc URL is set in `app.py` (`WORKOUT_DOC_ID`). For the export to work without login, the doc must be shared so **Anyone with the link can view** (or **Published to web**). If the fetch fails, the app shows a message and a link to open the document.

## Private links (confidentiality)

The app **requires a link** to open. Without a token in the URL, users see only a “use your link” message and no data.

1. Generate tokens and get shareable links:
   ```bash
   python generate_player_tokens.py https://your-app.onstreamlit.app
   ```
   This creates:
   - **data/player_tokens.json** – one token per player (private view).
   - **data/full_view_token.txt** – one token for the “see everyone” view (player selector, team stats, star of the week).

2. Share links:
   - **Full view** – Share only with coach/admin. Opens the full app (everyone’s data, player dropdown, star of the week).
   - **Per-player links** – Share each only with that player. They see only their name and their progress.

3. Commit and push **data/player_tokens.json** and **data/full_view_token.txt** so the deployed app can read them.

4. If someone removes the token from the URL, they only see the “use your link” page; they cannot reach the full view without the full-view token.

Regenerating tokens (run the script again) overwrites both files; old links stop working.

## Edit workouts (URL-based)

Editing the three workouts **for the current week only** is allowed only when the app is opened via **Begum’s** or **Fabio’s** private URL (the link that contains their `?token=...`). No password is used.

1. Open the app using Begum’s or Fabio’s personal link (from `docs/player_links.md` or the link shared with you).
2. An **Edit workouts (this week only)** section appears at the bottom: change titles and descriptions for Workout 1, 2, 3, then click **Save workouts for this week**. Data is written to `data/workouts.json` in the repo (or locally if no GitHub).
