import { tsiRows } from "@/components/game/odds-rows"
import { OddsTable } from "@/components/game/odds-table"
import type { Matchup } from "@/lib/api/types"

/**
 * TSI's prices for a hypothetical game: the fair line (no vig) and the TSI Book's price
 * (with vig). No Vegas column: books only post lines for scheduled games.
 */
export function MatchupOdds({ matchup }: { matchup: Matchup }) {
  const rows = tsiRows({
    markets: matchup.markets,
    home: matchup.home,
    away: matchup.away,
    projHome: matchup.proj_home,
    projAway: matchup.proj_away,
  })
  return <OddsTable title="TSI's line" rows={rows} vegas={false} />
}
