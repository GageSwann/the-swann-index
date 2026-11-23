"use client"

import type { RankingType } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const TABS: { value: RankingType; label: string }[] = [
  { value: "resume", label: "Résumé Rankings" },
  { value: "power", label: "Power Rankings" },
]

/**
 * The home page's one choice: which ranking drives the Top 25 lists and the games of the
 * week. Plain tabs (the active one underlined), with the week and when the rankings were
 * last updated across from them (owner, #160).
 */
export function RankingTabs({
  value,
  onChange,
  status,
}: {
  value: RankingType
  onChange: (value: RankingType) => void
  status: string | null // "Week 13, 2026. Updated Nov 23, 6:04 AM EST."
}) {
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
      {status && <p className="pb-2 text-sm text-muted-foreground">{status}</p>}
    </div>
  )
}
