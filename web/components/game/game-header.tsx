import type { GameSummary, TeamProfile } from "@/lib/api/types"
import { points } from "@/lib/format/numbers"
import { formatDay, formatKickoff } from "@/lib/format/time"

import { PhaseLabel, PhaseScope, When } from "./game-phase"
import { ScoreBoard } from "./score-board"

type Props = { game: GameSummary; home: TeamProfile | null; away: TeamProfile | null }

/** Both teams, records and ranks, kickoff, projected (or final) score, win probability.
 * After kickoff the viewer's clock switches it to "In progress", then "Final score
 * pending", with dashes for the score until the nightly run records it (13.5). */
export function GameHeader({ game, home, away }: Props) {
  const p = game.prediction
  const final = game.result?.final === true
  const when = game.kickoff
    ? `${formatDay(game.kickoff)}, ${formatKickoff(game.kickoff, game.kickoff_tbd)}`
    : "Date to be announced"
  const projected = (score: number | undefined) =>
    final ? undefined : (
      <>
        <When phase={["scheduled"]}>{score == null ? "–" : points(score)}</When>
        <When phase={["live", "pending"]}>—</When>
      </>
    )
  const tsiProjected =
    p &&
    `TSI projected ${game.away.school} ${points(p.proj_away)}, ${game.home.school} ${points(p.proj_home)}.`

  return (
    <PhaseScope game={{ kickoff: game.kickoff, tbd: game.kickoff_tbd, final, locked: p?.locked }}>
      <ScoreBoard
        away={{
          team: game.away,
          profile: away,
          score: final ? game.result?.away_points : p?.proj_away,
          shown: projected(p?.proj_away),
        }}
        home={{
          team: game.home,
          profile: home,
          score: final ? game.result?.home_points : p?.proj_home,
          shown: projected(p?.proj_home),
        }}
        neutral={game.neutral}
        context={
          <>
            {when}
            {game.neutral && ". Neutral site"}
            {game.notes && `. ${game.notes}`}
            <PhaseLabel prefix=". " />
          </>
        }
        note={
          p &&
          (final ? (
            tsiProjected
          ) : (
            <>
              <When phase={["scheduled"]}>
                Projected score and win probability from TSI&apos;s latest prediction.
              </When>
              <When phase={["live", "pending"]}>{tsiProjected}</When>
            </>
          ))
        }
        homeWinProb={p?.home_win_prob}
      />
    </PhaseScope>
  )
}
