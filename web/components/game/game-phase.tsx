"use client"

import { createContext, type ReactNode, useContext, useSyncExternalStore } from "react"

import {
  dataPhase,
  type GamePhase,
  gamePhase,
  PENDING_HINT,
  PHASE_LABEL,
  type PhaseInput,
} from "@/lib/game-phase"

/*
 * The viewer's clock flips games to "In progress" and later "Final score pending" (13.5)
 * without any request. One shared clock ticks every 30 s for the whole page. The server
 * render (and the first browser render, so hydration matches) uses what the data knows;
 * the clock takes over right after.
 */

const TICK_MS = 30_000
const listeners = new Set<() => void>()
let timer: ReturnType<typeof setInterval> | undefined
// Stable between ticks: React requires the same value for repeated reads.
let tick = typeof window === "undefined" ? 0 : Date.now()

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  if (timer === undefined) {
    tick = Date.now()
    timer = setInterval(() => {
      tick = Date.now()
      listeners.forEach((l) => l())
    }, TICK_MS)
  }
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) {
      clearInterval(timer)
      timer = undefined
    }
  }
}

const browserNow = () => tick
const serverNow = () => null

/** The game's phase by the viewer's clock (the data's phase until hydrated). */
export function useGamePhase(game: PhaseInput): GamePhase {
  const now = useSyncExternalStore(subscribe, browserNow, serverNow)
  return now === null ? dataPhase(game) : gamePhase(game, now)
}

const PhaseContext = createContext<GamePhase>("scheduled")

/** Gives the server-rendered parts inside it (`When`, `PhaseLabel`) the game's phase. */
export function PhaseScope({ game, children }: { game: PhaseInput; children: ReactNode }) {
  return <PhaseContext value={useGamePhase(game)}>{children}</PhaseContext>
}

/** Shows its children only in the listed phases. */
export function When({ phase, children }: { phase: GamePhase[]; children: ReactNode }) {
  return phase.includes(useContext(PhaseContext)) ? children : null
}

/** "In progress", "Final score pending" (with how it resolves) or "Final"; else nothing. */
export function PhaseLabel({
  phase,
  short = false,
  prefix = "",
}: {
  phase?: GamePhase // when used outside a PhaseScope
  short?: boolean // "Score pending" where space is tight
  prefix?: string
}) {
  const scoped = useContext(PhaseContext)
  const current = phase ?? scoped
  const label = current === "pending" && short ? "Score pending" : PHASE_LABEL[current]
  if (!label) return null
  return (
    <span title={current === "pending" ? PENDING_HINT : undefined}>
      {prefix}
      {label}
    </span>
  )
}
