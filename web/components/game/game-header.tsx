import type { GameSummary, TeamProfile } from "@/lib/api/types"
import { formatDay, formatKickoff } from "@/lib/format/time"

import { ScoreBoard } from "./score-board"

type Props = { game: GameSummary; home: TeamProfile | null; away: TeamProfile | null }

/** Both teams, records and ranks, kickoff, projected (or final) score, win probability. */
export function GameHeader({ game, home, away }: Props) {
  const p = game.prediction
  const final = game.result?.final === true
  const when = game.kickoff
    ? `${formatDay(game.kickoff)}, ${formatKickoff(game.kickoff, game.kickoff_tbd)}`
    : "Date to be announced"

  return (
    <ScoreBoard
      away={{
        team: game.away,
        profile: away,
        score: final ? game.result?.away_points : p?.proj_away,
      }}
      home={{
        team: game.home,
        profile: home,
        score: final ? game.result?.home_points : p?.proj_home,
      }}
      neutral={game.neutral}
      context={
        <>
          {when}
          {game.neutral && ". Neutral site"}
          {game.notes && `. ${game.notes}`}
          {final ? ". Final" : p?.locked ? ". In progress" : ""}
        </>
      }
      note={
        p &&
        (final
          ? `TSI projected ${game.away.school} ${Math.round(p.proj_away)}, ${game.home.school} ${Math.round(p.proj_home)}.`
          : "Projected score and win probability from TSI's latest prediction.")
      }
      homeWinProb={p?.home_win_prob}
    />
  )
}
