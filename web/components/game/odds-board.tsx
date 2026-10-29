import type { GameCenter } from "@/lib/api/types"

import { marketRows } from "./odds-rows"
import { OddsTable } from "./odds-table"

/** The game center's odds board: every market three ways, TSI plays outlined. */
export function OddsBoard({ center }: { center: GameCenter }) {
  const rows = marketRows(center)
  if (!rows) return null
  return (
    <OddsTable
      title="Odds board"
      rows={rows}
      vegas
      note={
        <>
          Vegas is the median of sportsbooks&apos; current lines (closing lines once the game
          starts). Team totals aren&apos;t in the market data yet.
        </>
      }
    />
  )
}
