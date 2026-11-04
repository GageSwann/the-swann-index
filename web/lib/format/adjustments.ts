import type { AdjustmentNote } from "@/lib/api/types"

import { signed } from "./numbers"

/** "Ohio State offense −4.0 (QB out)": one manual adjustment, points per game. */
export function describeAdjustment(note: AdjustmentNote): string {
  const sides = [
    note.off_points !== 0 && `offense ${signed(note.off_points)}`,
    note.def_points !== 0 && `defense ${signed(note.def_points)}`,
  ].filter(Boolean)
  return `${note.school} ${sides.join(", ")} (${note.reason})`
}
