"use client"

import { useState } from "react"

import type { GameOfWeekView, RankedTeam, RankingType } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"

import { GameOfWeekCard } from "./game-of-week"
import { RankingTabs } from "./ranking-tabs"
import { RankingsRail } from "./rankings-rail"

type PerType<T> = Record<RankingType, T>
type Pick = { pick: GameOfWeekView | null; when: string | null }
export type HomePicks = Record<Division, PerType<Pick>>

type Props = {
  rails: Record<Division, PerType<RankedTeam[]>>
  picks: HomePicks
}

const LABEL: Record<RankingType, string> = { power: "Power", resume: "Résumé" }

/**
 * The home page (Phase 13.4): the FBS and FCS games of the week in the middle, each
 * division's Top 25 in a side rail. One ranking choice (Power or Résumé) drives both. On
 * desktop the three columns share one height, so the cards and the lists end level.
 * Phones: games first, then the lists.
 */
export function HomeView({ rails, picks }: Props) {
  const [type, setType] = useState<RankingType>("power")
  return (
    <div className="space-y-6">
      <RankingTabs value={type} onChange={setType} />
      <div
        id="home-rankings"
        className="grid gap-8 lg:grid-cols-[15.5rem_minmax(0,1fr)_15.5rem] xl:grid-cols-[18rem_minmax(0,1fr)_18rem]"
      >
        <div className="flex min-w-0 flex-col gap-6 lg:col-start-2 lg:row-start-1">
          <GameOfWeekCard division="fbs" type={type} teams={rails.fbs[type]} {...picks.fbs[type]} />
          <GameOfWeekCard
            division="fcs"
            type={type}
            teams={rails.fcs[type]}
            className="flex-1"
            {...picks.fcs[type]}
          />
        </div>
        <div className="grid min-w-0 gap-8 sm:grid-cols-2 lg:contents">
          <div className="min-w-0 lg:col-start-1 lg:row-start-1">
            <RankingsRail
              id="fbs"
              title={`FBS ${LABEL[type]} Top 25`}
              teams={rails.fbs[type]}
              href="/rankings"
            />
          </div>
          <div className="min-w-0 lg:col-start-3 lg:row-start-1">
            <RankingsRail
              id="fcs"
              title={`FCS ${LABEL[type]} Top 25`}
              teams={rails.fcs[type]}
              href="/rankings/fcs"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
