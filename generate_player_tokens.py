#!/usr/bin/env python3
"""
Generate unique secret tokens per player and one for the full view (everyone).
Run once, then share each link only with that player; share the full-view link only with people who may see everyone.

Usage:
  python generate_player_tokens.py [BASE_URL]

  BASE_URL = base URL of your app (e.g. https://your-app.onstreamlit.app or http://localhost:8501)
  If omitted, prints URLs with a placeholder you can replace.

Output:
  - Overwrites data/player_tokens.json (token -> player name).
  - Overwrites data/full_view_token.txt (single token for the "see everyone" view).
  - Prints the full-view URL and one private URL per player.
"""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
TOKENS_FILE = DATA_DIR / "player_tokens.json"
FULL_VIEW_TOKEN_FILE = DATA_DIR / "full_view_token.txt"


def main() -> None:
    base_url = (sys.argv[1] or "").rstrip("/").strip()
    if not base_url:
        base_url = "https://YOUR-APP-URL-HERE"

    if not PLAYERS_FILE.exists():
        print(f"Error: {PLAYERS_FILE} not found. Add players first.")
        sys.exit(1)

    with open(PLAYERS_FILE, encoding="utf-8") as f:
        players = json.load(f)
    if not isinstance(players, list) or not players:
        print("Error: players.json must be a non-empty list of names.")
        sys.exit(1)

    token_to_player = {}
    for name in players:
        token = secrets.token_urlsafe(16)
        token_to_player[token] = name

    full_view_token = secrets.token_urlsafe(16)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(token_to_player, f, indent=2)
    with open(FULL_VIEW_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(full_view_token)

    print("Generated data/player_tokens.json and data/full_view_token.txt")
    print()
    full_view_url = f"{base_url}/?token={full_view_token}"
    print("Full view (everyone) – share only with coach/admin:")
    print(f"  {full_view_url}")
    print()
    print("Private links (share each only with that player):")
    print("-" * 60)
    for name in players:
        token = next(t for t, p in token_to_player.items() if p == name)
        url = f"{base_url}/?token={token}"
        print(f"  {name}: {url}")
    print("-" * 60)
    if "YOUR-APP-URL" in base_url:
        print("Replace BASE_URL with your real app URL and run again to re-print links,")
        print("or share links after replacing the base in the URLs above.")


if __name__ == "__main__":
    main()
