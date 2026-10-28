"""Weekly review of The Swann Index from the public API (no secrets, stdlib only).

Prints a Markdown report: data freshness, the TSI Book (season + the week's graded
picks), prediction accuracy for the week vs. the closing line, Power rankings with
weekly movement, and the coming week's key matchups.

    python weekly_review.py                      # production API, last completed week
    python weekly_review.py --week 8             # a specific week
    python weekly_review.py --api http://127.0.0.1:8000   # local API (dev branch)

Spread sign: home team's view, negative = home favored (CLAUDE.md, data conventions).
"""

import argparse
import json
import sys
import urllib.request
from statistics import mean

PRODUCTION_API = "https://tsi-api-44wx.onrender.com"


def get(api: str, path: str):
    # The free Render API sleeps when idle; the first call can take ~1 minute.
    with urllib.request.urlopen(api + path, timeout=150) as r:
        return json.load(r)


def short(team: dict) -> str:
    return team.get("abbreviation") or team["school"]


def ranked(team: dict, ranks: dict) -> str:
    r = ranks.get(team["slug"])
    return f"#{r} {team['school']}" if r and r <= 25 else team["school"]


def fmt_record(r: dict) -> str:
    return f"{r['wins']}-{r['losses']}" + (f"-{r['pushes']}" if r.get("pushes") else "")


def book_section(api: str, season: int, week_ids: set[int], week: int) -> list[str]:
    ledger = get(api, f"/book/ledger?season={season}")
    out = ["## TSI Book", ""]
    overall = next((r for r in ledger["records"] if r["market"] == "all" and r["tier"] == 0), None)
    if overall and overall["wins"] + overall["losses"] + overall["pushes"]:
        clv = "n/a" if overall["clv"] is None else f"{overall['clv']:+.2f} pts"
        beat = "" if overall["beat_close"] is None else f", beat the close {overall['beat_close']:.0%}"
        out.append(
            f"- **Season:** {fmt_record(overall)}, {overall['units']:+.2f}u flat "
            f"({overall['roi']:+.1%} ROI), ¼ Kelly {overall['kelly_units']:+.2f}u, CLV {clv}{beat}"
        )
    else:
        out.append("- **Season:** no graded picks yet")
    week_picks = [p for p in ledger["picks"] if p["game_id"] in week_ids]
    graded = [p for p in week_picks if p["status"] == "graded"]
    if week_picks:
        won = sum(p["pick"]["units_won"] or 0 for p in graded)
        wl = [p["pick"]["result"] for p in graded]
        out.append(
            f"- **Week {week}:** {wl.count('win')}-{wl.count('loss')}"
            + (f"-{wl.count('push')}" if wl.count("push") else "")
            + f", {won:+.2f}u ({len(week_picks) - len(graded)} not graded yet)"
        )
        out += ["", "| Game | Pick | Result | Close | CLV |", "|---|---|---|---|---|"]
        for p in sorted(week_picks, key=lambda p: p["kickoff"] or ""):
            k = p["pick"]
            line = k["line"] if k["line"] is not None else ""
            pick = f"{'★' * k['tier']} {k['market']} {k['side']} {line}".strip()
            res = (k["result"] or p["status"]) + (
                f" {k['units_won']:+.2f}u" if k["units_won"] is not None else ""
            )
            clv = "" if k["clv"] is None else f"{k['clv']:+.2f}"
            close = "" if k["closing_line"] is None else k["closing_line"]
            out.append(f"| {p['away']['school']} at {p['home']['school']} | {pick} | {res} | {close} | {clv} |")
    else:
        out.append(f"- **Week {week}:** no picks")
    return out + [""]


def accuracy_section(games: list[dict], week: int) -> list[str]:
    rows = []
    for g in games:
        p, r, m = g.get("prediction"), g.get("result"), g.get("market") or {}
        if not (p and r and r.get("final") and p.get("locked")):
            continue
        margin = r["home_points"] - r["away_points"]
        vegas = -m["spread"] if m.get("spread") is not None else None
        rows.append((g, margin, -p["spread"], vegas, r["home_points"] + r["away_points"], p["total"], m.get("total")))
    out = [f"## Week {week} predictions vs. results", ""]
    if not rows:
        return out + ["No finished games with a locked TSI prediction.", ""]
    n = len(rows)
    tsi_mae = mean(abs(t - mg) for _, mg, t, *_ in rows)
    with_line = [(mg, t, v) for _, mg, t, v, *_ in rows if v is not None]
    su = lambda pairs: sum((x > 0) == (mg > 0) for mg, x in pairs if mg != 0 and x != 0)
    ats = [(t > v) == (mg > v) for mg, t, v in with_line if mg != v and t != v]
    tot = [(tt, pt, mt) for *_, tt, pt, mt in rows]
    out.append(f"- **Games:** {n} finished with a locked prediction")
    if with_line:
        vegas_mae = mean(abs(v - mg) for mg, _, v in with_line)
        out.append(f"- **Margin error:** TSI {tsi_mae:.2f} vs. Vegas close {vegas_mae:.2f} (backtest gap ≈ 0.4)")
        out.append(
            f"- **Winners:** TSI {su([(mg, t) for mg, t, _ in with_line])}, "
            f"Vegas {su([(mg, v) for mg, _, v in with_line])} of {len(with_line)}"
        )
        out.append(f"- **TSI's side vs. the closing spread:** {sum(ats)}-{len(ats) - sum(ats)} (TSI has no edge here by design)")
    else:
        out.append(f"- **Margin error:** TSI {tsi_mae:.2f} (no closing lines)")
    tm = [(abs(pt - tt), abs(mt - tt)) for tt, pt, mt in tot if mt is not None]
    if tm:
        out.append(f"- **Total error:** TSI {mean(a for a, _ in tm):.2f} vs. Vegas {mean(b for _, b in tm):.2f}")
    out += ["", "Biggest TSI misses (home view; + = home won by):", ""]
    for g, mg, t, v, *_ in sorted(rows, key=lambda x: -abs(x[2] - x[1]))[:5]:
        vs = "" if v is None else f", Vegas {v:+.1f}"
        out.append(f"- {g['away']['school']} at {g['home']['school']}: TSI {t:+.1f}{vs}, actual {mg:+d}")
    return out + [""]


def rankings_section(api: str) -> tuple[list[str], dict]:
    data = get(api, "/rankings")
    ranks = {t["team"]["slug"]: t["rank"] for t in data["teams"]}
    since = (data.get("previous_as_of") or "")[:10] or "n/a"
    out = [f"## Power rankings (movement since {since})", "", "| # | Team | Record | Rating | Move |", "|---|---|---|---|---|"]
    for t in data["teams"][:25]:
        prev = t.get("previous_rank")
        move = "new" if prev is None else ("—" if prev == t["rank"] else f"{'▲' if prev > t['rank'] else '▼'}{abs(prev - t['rank'])}")
        out.append(f"| {t['rank']} | {t['team']['school']} | {t['wins']}-{t['losses']} | {t['rating']:+.1f} | {move} |")
    moved = [(t["previous_rank"] - t["rank"], t["team"]["school"]) for t in data["teams"] if t.get("previous_rank")]
    if moved:
        moved.sort()
        out += ["", f"Risers: {', '.join(f'{n} (+{d})' for d, n in moved[::-1][:5])}",
                f"Fallers: {', '.join(f'{n} ({d})' for d, n in moved[:5])}"]
    return out + [""], ranks


def next_week_section(api: str, season: int, week: int, ranks: dict) -> list[str]:
    try:
        games = get(api, f"/weeks/{season}/{week}/games")["games"]
    except Exception:  # noqa: BLE001 - no such week (end of season)
        return []
    pub = [g for g in games if g.get("prediction")]
    out = [f"## Week {week} preview", "", f"{len(pub)} of {len(games)} games have TSI predictions.", ""]

    def line(g):
        p, m = g["prediction"], g.get("market") or {}
        fav = g["home"] if p["spread"] < 0 else g["away"]
        mk = f" | Vegas {m['spread']:+.1f}, total {m['total']}" if m.get("spread") is not None else ""
        picks = "".join(f" | PLAY {'★' * k['tier']} {k['market']} {k['side']} {k['line']}" for k in p["picks"])
        return (f"- {ranked(g['away'], ranks)} {'vs' if g['neutral'] else 'at'} {ranked(g['home'], ranks)}: "
                f"{short(fav)} by {abs(p['spread']):.1f}, total {p['total']:.1f}{mk}{picks}")

    top = lambda g, side: ranks.get(g[side]["slug"], 99) <= 25
    both = [g for g in pub if top(g, "home") and top(g, "away")]
    plays = [g for g in pub if g["prediction"]["picks"]]
    lined = [g for g in pub if (g.get("market") or {}).get("spread") is not None]
    dis = sorted(lined, key=lambda g: -abs(g["prediction"]["spread"] - g["market"]["spread"]))[:4]
    for title, items in (("Ranked vs. ranked", both), ("TSI plays", plays), ("Biggest disagreements with Vegas", dis)):
        out += [f"**{title}:**", ""] + ([line(g) for g in items] or ["- none"]) + [""]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--api", default=PRODUCTION_API, help="API base URL (default: production)")
    ap.add_argument("--season", type=int, help="default: the current season")
    ap.add_argument("--week", type=int, help="week to review (default: the last completed week)")
    args = ap.parse_args()
    api = args.api.rstrip("/")

    meta = get(api, "/meta/current")
    season = args.season or meta["season"]
    week = args.week or max(1, meta["week"] - 1)
    games = get(api, f"/weeks/{season}/{week}/games")["games"]

    report = [
        f"# TSI weekly review: {season}, week {week}",
        "",
        (
            f"Data: ratings updated {meta['ratings_updated_at']}, predictions published "
            f"{meta['predictions_published_at']}, model {meta['model_version']} (API: {api})"
        ),
        "",
    ]
    report += book_section(api, season, {g["id"] for g in games}, week)
    report += accuracy_section(games, week)
    rank_lines, ranks = rankings_section(api)
    report += rank_lines
    report += next_week_section(api, season, week + 1, ranks)
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
