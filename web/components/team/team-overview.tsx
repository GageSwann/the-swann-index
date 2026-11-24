import { GameOfWeekCard } from "@/components/home/game-of-week"
import type { GameOdds } from "@/lib/api/schedule-odds"
import type { RankedTeam, TeamProfile } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { gameWhen } from "@/lib/format/time"

import { RankNeighbors } from "./rank-neighbors"
import { ScheduleList } from "./schedule-list"

/**
 * Under the team header (owner, #199): the schedule as a vertical list (left), the Next Game
 * card, the same card as the home page's Game of the Week (center), and where the team stands
 * in the Résumé and Power rankings with its neighbors (right). The same three columns as the
 * home page; phones: the card, the rankings, then the schedule.
 */
export function TeamOverview({
  profile,
  odds,
  ranked,
  division,
}: {
  profile: TeamProfile
  odds: Map<number, GameOdds>
  ranked: RankedTeam[] // the team's division, both ranks per team
  division: Division
}) {
  const card = profile.next_game ?? null
  const final = !!card?.game.result?.final
  // The card's ranks: Résumé, like the home page's default, within the team's division.
  const resumeTop = ranked.flatMap((t) =>
    t.rank_resume != null && t.rank_resume <= 25 ? [{ team: t.team, rank: t.rank_resume }] : [],
  )
  return (
    <div className="grid gap-8 lg:grid-cols-[15.5rem_minmax(0,1fr)_15.5rem] xl:grid-cols-[18rem_minmax(0,1fr)_18rem]">
      <div className="min-w-0 lg:col-start-2 lg:row-start-1">
        <GameOfWeekCard
          id="next-game"
          title={final ? "Last Game" : "Next Game"}
          pick={card}
          teams={resumeTop}
          division={division}
          when={card ? gameWhen(card.game) : null}
          empty="No games on the schedule yet."
          className="h-full"
        />
      </div>
      <div className="min-w-0 lg:col-start-3 lg:row-start-1">
        <RankNeighbors ranked={ranked} slug={profile.team.slug} division={division} />
      </div>
      <div className="min-w-0 lg:col-start-1 lg:row-start-1">
        <ScheduleList
          schedule={profile.schedule}
          odds={odds}
          nextId={card && !final ? card.game.id : null}
        />
      </div>
    </div>
  )
}
