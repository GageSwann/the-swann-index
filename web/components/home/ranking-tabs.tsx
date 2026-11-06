"use client"

import type { RankingType } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const TABS: { value: RankingType; label: string; about: string }[] = [
  {
    value: "power",
    label: "Power Rankings",
    about: "Power ranks teams by how well they have played this season.",
  },
  {
    value: "resume",
    label: "Résumé Rankings",
    about:
      "Résumé ranks teams by what they have accomplished: their record against their schedule.",
  },
]

/**
 * The home page's one choice: which ranking drives the Top 25 lists and the games of the
 * week. Plain tabs (the active one underlined), with one sentence on what the active
 * ranking measures.
 */
export function RankingTabs({
  value,
  onChange,
}: {
  value: RankingType
  onChange: (value: RankingType) => void
}) {
  const active = TABS.find((t) => t.value === value)!
  return (
    <div className="flex flex-col gap-x-8 gap-y-2 border-b border-border md:flex-row md:items-end md:justify-between">
      <div role="group" aria-label="Rank teams by" className="flex gap-6">
        {TABS.map((t) => {
          const on = t.value === value
          return (
            <button
              key={t.value}
              type="button"
              aria-pressed={on}
              aria-controls="home-rankings"
              onClick={() => onChange(t.value)}
              className={cn(
                "-mb-px border-b-2 pb-2 text-[15px] font-medium transition-colors",
                on
                  ? "border-foreground text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          )
        })}
      </div>
      <p className="pb-2 text-sm text-muted-foreground" aria-live="polite">
        {active.about}
      </p>
    </div>
  )
}
