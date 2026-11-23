"use client"

import type { RankingType } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { cn } from "@/lib/utils"

const TABS: { value: RankingType; label: string }[] = [
  { value: "resume", label: "Résumé" },
  { value: "power", label: "Power" },
]

const DIVISIONS: { value: Division; label: string }[] = [
  { value: "fbs", label: "FBS" },
  { value: "fcs", label: "FCS" },
]

/**
 * The home page's controls: which ranking drives the Top 25 lists and the games of the
 * week (plain tabs, the active one underlined; "Rankings" joins the label from `sm` up),
 * and on phones and tablets which division is shown (#163; desktop shows both). Below or
 * beside them: the week and when the rankings were last updated (#160).
 */
export function RankingTabs({
  value,
  onChange,
  division,
  onDivision,
  status,
}: {
  value: RankingType
  onChange: (value: RankingType) => void
  division: Division
  onDivision: (value: Division) => void
  status: string | null // "Week 13, 2026. Updated Nov 23, 6:04 AM EST."
}) {
  return (
    <div className="space-y-2 lg:flex lg:items-end lg:justify-between lg:gap-8 lg:space-y-0 lg:border-b lg:border-border">
      <div className="flex items-end justify-between gap-4 border-b border-border lg:border-0">
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
                <span className="hidden sm:inline"> Rankings</span>
              </button>
            )
          })}
        </div>
        {/* Phones and tablets show one division at a time; desktop has room for both. */}
        <div
          role="group"
          aria-label="Division"
          className="mb-2 flex rounded-md border border-border p-0.5 lg:hidden"
        >
          {DIVISIONS.map((d) => {
            const on = d.value === division
            return (
              <button
                key={d.value}
                type="button"
                aria-pressed={on}
                aria-controls="home-rankings"
                onClick={() => onDivision(d.value)}
                className={cn(
                  "min-w-12 rounded-sm px-3 py-1 text-sm font-medium transition-colors",
                  on ? "bg-primary text-primary-foreground" : "text-muted-foreground",
                )}
              >
                {d.label}
              </button>
            )
          })}
        </div>
      </div>
      {status && <p className="text-xs text-muted-foreground lg:pb-2 lg:text-sm">{status}</p>}
    </div>
  )
}
