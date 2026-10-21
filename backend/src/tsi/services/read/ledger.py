"""`/book/ledger`: the TSI Book's official picks for a season, record, units, CLV.

Official = the picks on each game's locked (latest pre-kickoff) snapshot. Picks on
games not yet started are listed as `open` from the latest snapshot: they can
still change until kickoff.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from tsi.db.queries.games import season_games
from tsi.db.queries.snapshots import picks_for_snapshots, snapshots_for_season
from tsi.db.queries.team_info import TeamRef, team_refs
from tsi.services.read.common import PickView, current_snapshot, pick_view

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class LedgerPick:
    game_id: int
    kickoff: datetime | None
    home: TeamRef
    away: TeamRef
    published_at: datetime
    status: str  # 'open' (may still change) | 'pending' (locked, not graded) | 'graded'
    pick: PickView


@dataclass(frozen=True)
class LedgerRecord:
    market: str  # 'all' or a market
    tier: int  # 0 = all tiers
    wins: int
    losses: int
    pushes: int
    units: float  # flat stakes
    kelly_units: float
    roi: float  # units per bet
    clv: float | None  # mean CLV of spread/total picks (points)
    beat_close: float | None  # share of those with CLV > 0


@dataclass(frozen=True)
class UnitsPoint:
    date: date
    units: float  # cumulative flat units
    kelly_units: float


@dataclass(frozen=True)
class Ledger:
    season: int
    records: list[LedgerRecord]
    cumulative: list[UnitsPoint]
    picks: list[LedgerPick]  # newest kickoff first


def ledger(session: Session, season: int, now: datetime) -> Ledger:
    snaps = snapshots_for_season(session, season)
    games = {g.id: g for g in season_games(session, season, list(snaps))}
    shown = {}
    for gid, game_snaps in snaps.items():
        g = games.get(gid)
        snap, locked = current_snapshot(game_snaps, g.start_time if g else None, now)
        if snap is not None:
            shown[gid] = (snap, locked)
    picks = picks_for_snapshots(session, [s.id for s, _ in shown.values()])
    refs = team_refs(session, season, {t for g in games.values() for t in (g.home_id, g.away_id)})

    rows: list[LedgerPick] = []
    for gid, (snap, locked) in shown.items():
        g = games[gid]
        for p in picks.get(snap.id, []):
            view = pick_view(p)
            status = "graded" if view.result else "pending" if locked else "open"
            rows.append(
                LedgerPick(
                    gid,
                    g.start_time,
                    refs[g.home_id],
                    refs[g.away_id],
                    snap.published_at,
                    status,
                    view,
                )
            )
    rows.sort(key=lambda r: (r.kickoff is None, r.kickoff), reverse=True)
    graded = [r for r in rows if r.status == "graded"]
    return Ledger(season, _records(graded), _cumulative(graded), rows)


def _records(graded: list[LedgerPick]) -> list[LedgerRecord]:
    groups = [("all", 0, graded)]
    for market in sorted({r.pick.market for r in graded}):
        in_market = [r for r in graded if r.pick.market == market]
        groups.append((market, 0, in_market))
        groups += [(market, t, [r for r in in_market if r.pick.tier == t]) for t in (1, 2, 3)]
    return [_record(m, t, g) for m, t, g in groups if g or m == "all"]


def _record(market: str, tier: int, picks: list[LedgerPick]) -> LedgerRecord:
    units = sum(r.pick.units_won or 0.0 for r in picks)
    kelly = sum((r.pick.units_won or 0.0) * (r.pick.kelly_units or 0.0) for r in picks)
    clvs = [r.pick.clv for r in picks if r.pick.clv is not None and r.pick.market != "ml"]
    return LedgerRecord(
        market=market,
        tier=tier,
        wins=sum(r.pick.result == "win" for r in picks),
        losses=sum(r.pick.result == "loss" for r in picks),
        pushes=sum(r.pick.result == "push" for r in picks),
        units=units,
        kelly_units=kelly,
        roi=units / len(picks) if picks else 0.0,
        clv=sum(clvs) / len(clvs) if clvs else None,
        beat_close=sum(c > 0 for c in clvs) / len(clvs) if clvs else None,
    )


def _cumulative(graded: list[LedgerPick]) -> list[UnitsPoint]:
    flat = kelly = 0.0
    by_day: dict[date, tuple[float, float]] = {}
    for r in sorted(graded, key=lambda r: r.kickoff or EPOCH):
        flat += r.pick.units_won or 0.0
        kelly += (r.pick.units_won or 0.0) * (r.pick.kelly_units or 0.0)
        if r.kickoff is not None:
            by_day[r.kickoff.date()] = (flat, kelly)
    return [UnitsPoint(d, f, k) for d, (f, k) in sorted(by_day.items())]
