import type { GameSummary, SnapshotPoint } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { favoriteLine } from "@/lib/format/odds"
import { formatUpdated } from "@/lib/format/time"

/** Every published TSI prediction for the game, oldest first (they are never edited). */
export function PredictionHistory({
  game,
  history,
}: {
  game: GameSummary
  history: SnapshotPoint[]
}) {
  if (history.length === 0) return null
  const first = history[0]
  const last = history[history.length - 1]
  // Compare the lines as shown (one decimal), so sub-display changes don't read as a move.
  const moved = history.length > 1 && first.spread.toFixed(1) !== last.spread.toFixed(1)

  return (
    <section aria-labelledby="history-heading" className="space-y-3">
      <h2 id="history-heading" className="text-2xl font-semibold font-stretch-condensed">
        Prediction history
      </h2>
      <p className="text-sm text-muted-foreground">
        {moved
          ? `TSI's line moved from ${favoriteLine(first.spread, game.home, game.away)} to ${favoriteLine(last.spread, game.home, game.away)}.`
          : history.length > 1
            ? "TSI's line hasn't moved since it was first published."
            : "Published once. A new snapshot is added whenever the prediction or the Book's picks change."}
      </p>
      <ol className="divide-y divide-border rounded-md border border-border text-sm">
        {history.map((s) => (
          <li
            key={s.published_at}
            className="flex flex-wrap justify-between gap-x-4 gap-y-1 px-3 py-2"
          >
            <span className="text-muted-foreground">{formatUpdated(s.published_at)}</span>
            <span>
              {favoriteLine(s.spread, game.home, game.away)}, total {s.total.toFixed(1)},{" "}
              {game.home.abbreviation ?? game.home.school} {percent(s.home_win_prob, 0)} to win
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}
