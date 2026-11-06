"use client"

import { useState } from "react"

import { Segmented } from "@/components/ui/segmented"
import type { GameOfWeekView, RankedTeam, RankingType } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"

import { GameOfWeekCard } from "./game-of-week"
import { RankingsRail } from "./rankings-rail"

type PerType<T> = Record<RankingType, T>
type Pick = { pick: GameOfWeekView | null; when: string | null }
export type HomePicks = Record<Division, PerType<Pick>>

type Props = {
  rails: Record<Division, PerType<RankedTeam[]>>
  picks: HomePicks
}

const TYPES: { value: RankingType; label: string }[] = [
  { value: "power", label: "Power" },
  { value: "resume", label: "Résumé" },
]

const EXPLAIN: Record<RankingType, string> = {
  power: "Power: who's best right now, from this season's games.",
  resume: "Résumé: who has earned it, by record against schedule.",
}

/**
 * The home page (Phase 13.4): FBS and FCS games of the week in the middle, each
 * division's Top 25 in a side rail. One Power / Résumé toggle switches both the rails and
 * the games. Phones: games first, then the rails.
 */
export function HomeView({ rails, picks }: Props) {
  const [type, setType] = useState<RankingType>("power")
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Segmented label="Ranking" value={type} onChange={setType} options={TYPES} />
        <p className="text-sm text-muted-foreground">{EXPLAIN[type]}</p>
      </div>
      <div className="grid gap-8 lg:grid-cols-[15.5rem_minmax(0,1fr)_15.5rem] xl:grid-cols-[18rem_minmax(0,1fr)_18rem]">
        <div className="min-w-0 space-y-6 lg:col-start-2 lg:row-start-1">
          <GameOfWeekCard
            division="fbs"
            type={type}
            size="lead"
            teams={rails.fbs[type]}
            {...picks.fbs[type]}
          />
          <GameOfWeekCard
            division="fcs"
            type={type}
            size="second"
            teams={rails.fcs[type]}
            {...picks.fcs[type]}
          />
        </div>
        <div className="grid min-w-0 gap-8 sm:grid-cols-2 lg:contents">
          <div className="min-w-0 lg:col-start-1 lg:row-start-1">
            <RankingsRail
              title="FBS Top 25"
              teams={rails.fbs[type]}
              href="/rankings"
              linkLabel="All FBS rankings"
            />
          </div>
          <div className="min-w-0 lg:col-start-3 lg:row-start-1">
            <RankingsRail
              title="FCS Top 25"
              teams={rails.fcs[type]}
              href="/rankings/fcs"
              linkLabel="All FCS rankings"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
