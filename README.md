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
- **data/workouts.json** – Workouts **per week**: key = week start date (`YYYY-MM-DD`, Monday); value = `{ "workout_1", "workout_2", "workout_3" }` (each with `title` and `description`). Workout 1/2/3 are shown in the popovers; editing applies only to the current week.
- **data/completions.json** – Who completed which day (`YYYY-MM-DD` → list of player names). Updated when someone checks the box.

Edit `players.json` in the repo (or in `data/`). Workouts can be edited **in the app** (see below) or by editing `workouts.json` in the repo.

## Edit workouts (password-protected)

To edit the three workouts **for the current week only** (other weeks stay unchanged):

1. Add **EDITOR_PASSWORD** to Secrets (Streamlit Cloud) or to `.streamlit/secrets.toml` (local). Use a password only the editor (e.g. coach) should know.
2. In the app sidebar, enter the password and click **Unlock editing**.
3. An **Edit workouts (this week only)** section appears: change titles and descriptions for Workout 1, 2, 3, then click **Save workouts for this week**. Data is written to `data/workouts.json` in the repo (or locally if no GitHub).
4. Click **Lock editing** in the sidebar to hide the form again.
