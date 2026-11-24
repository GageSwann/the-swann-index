import { useSyncExternalStore } from "react"

import type { DivisionView } from "@/lib/divisions"

/**
 * The Rankings page's filters (Top 25 / all teams, conference), per division, shared by its
 * Résumé and Power pages (#206): switching between them keeps the filters. Kept in the
 * browser for the visit (an external store, so every copy of the page, including ones kept
 * alive in the background, reads the same values); a fresh load starts from the defaults.
 */
export type RankingsFilters = { scope: "top25" | "all"; conference: string }

const DEFAULT: RankingsFilters = { scope: "top25", conference: "" }
const filters = new Map<DivisionView, RankingsFilters>()
const listeners = new Set<() => void>()

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useRankingsFilters(
  division: DivisionView,
): [RankingsFilters, (change: Partial<RankingsFilters>) => void] {
  const value = useSyncExternalStore(
    subscribe,
    () => filters.get(division) ?? DEFAULT,
    () => DEFAULT,
  )
  const update = (change: Partial<RankingsFilters>) => {
    filters.set(division, { ...(filters.get(division) ?? DEFAULT), ...change })
    listeners.forEach((listener) => listener())
  }
  return [value, update]
}
