"use client"

import type { RankingType } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const OPTIONS: { value: RankingType; label: string; hint: string }[] = [
  { value: "power", label: "Power", hint: "Who's best right now" },
  { value: "resume", label: "Résumé", hint: "Who's earned it" },
]

/**
 * The home page's one choice (Phase 13.4): which ranking drives the Top 25 lists and the
 * games of the week. Each option says what it means, so no separate explanation is needed.
 */
export function RankingSwitch({
  value,
  onChange,
}: {
  value: RankingType
  onChange: (value: RankingType) => void
}) {
  return (
    <div
      role="group"
      aria-label="Rank teams by"
      className="grid w-full grid-cols-2 gap-2 sm:inline-grid sm:w-auto"
    >
      {OPTIONS.map((o) => {
        const on = value === o.value
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(o.value)}
            className={cn(
              "flex flex-col items-start rounded-md border px-4 py-2.5 text-left transition-colors sm:min-w-52",
              on
                ? "tsi-lit border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-foreground hover:border-foreground",
            )}
          >
            <span className="text-lg leading-tight font-semibold font-stretch-condensed">
              {o.label}
            </span>
            <span
              className={cn("text-sm", on ? "text-primary-foreground/80" : "text-muted-foreground")}
            >
              {o.hint}
            </span>
          </button>
        )
      })}
    </div>
  )
}
