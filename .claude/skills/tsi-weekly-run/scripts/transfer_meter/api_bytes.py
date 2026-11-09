"""usage (from backend/, API up via serve_relay.py):
    PYTHONPATH=<this dir> uv run python api_bytes.py

DB bytes per API request (local API on :8001 through the relay). Each URL twice: cold, warm."""

import json
import urllib.request

from meterlib import counters

API = "http://127.0.0.1:8001"


def get(path):
    d0, _, c0 = counters()
    with urllib.request.urlopen(API + path, timeout=300) as r:
        body = r.read()
    d1, _, c1 = counters()
    return d1 - d0, len(body), json.loads(body) if body[:1] in b"{[" else None


meta = get("/meta/current")[2]
season, week = meta["season"], meta["week"]
rank = get("/rankings?type=power&division=fbs")[2]
slug = rank["teams"][0]["team"]["slug"]
fcs_slug = get("/rankings?type=power&division=fcs")[2]["teams"][0]["team"]["slug"]
board = get(f"/weeks/{season}/{week}/games?division=fbs")[2]
games = board["games"] if isinstance(board, dict) else board
game_id = games[0]["id"] if "id" in games[0] else games[0]["game_id"]

paths = [
    "/meta/current",
    "/games-of-week",
    "/rankings?type=power&division=fbs",
    "/rankings?type=resume&division=fbs",
    "/rankings?type=power&division=fcs",
    "/rankings?type=power&division=all",
    "/teams?division=fbs",
    f"/teams/{slug}",
    f"/teams/{fcs_slug}",
    f"/weeks/{season}/{week}/games?division=fbs",
    f"/weeks/{season}/{week}/games?division=fcs",
    f"/weeks/{season}/{week}/games?division=all",
    f"/weeks/{season}/{week - 3}/games?division=fbs",
    f"/games/{game_id}",
    "/playoff?division=fbs",
    "/playoff?division=fcs",
    f"/matchup?home={slug}&away={fcs_slug}",
]
print(f"{'path':55} {'cold KB':>9} {'warm KB':>9} {'resp KB':>8}")
for p in paths:
    cold, size, _ = get(p)
    warm, _, _ = get(p)
    print(f"{p:55} {cold / 1e3:9.1f} {warm / 1e3:9.1f} {size / 1e3:8.1f}")
