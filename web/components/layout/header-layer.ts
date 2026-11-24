import { useSyncExternalStore } from "react"

/**
 * Whether the header search is open, shared with the sport menus so only one header dropdown
 * shows at a time (owner, #193): while search is open the sport menus don't open on hover,
 * and opening search closes an open sport menu. `opens` counts how often search has opened,
 * so a menu opened before the latest search stays closed afterwards (no effect needed).
 */
export type SearchLayer = { open: boolean; opens: number }

let state: SearchLayer = { open: false, opens: 0 }
const listeners = new Set<() => void>()

export function setSearchOpen(open: boolean): void {
  if (open === state.open) return
  state = { open, opens: state.opens + (open ? 1 : 0) }
  listeners.forEach((listener) => listener())
}

export function searchLayer(): SearchLayer {
  return state
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

const SERVER: SearchLayer = { open: false, opens: 0 }

export function useSearchLayer(): SearchLayer {
  return useSyncExternalStore(subscribe, searchLayer, () => SERVER)
}
