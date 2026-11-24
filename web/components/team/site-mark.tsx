import type { ScheduleGame } from "@/lib/api/types"

const MARK: Record<string, { mark: string; spoken: string }> = {
  home: { mark: "vs", spoken: "vs." },
  away: { mark: "at", spoken: "at" },
}

/**
 * A neutral field's mark: a small outlined "N" (#208), on the team schedules and between the
 * teams on every game card (#209). Hover says "Neutral site"; screen readers hear it too.
 */
export function NeutralTag({ className }: { className?: string }) {
  return (
    <span title="Neutral site" className={className}>
      <span
        aria-hidden
        className="rounded-sm border border-border px-1 text-[0.625rem] leading-4 font-semibold text-muted-foreground"
      >
        N
      </span>
      <span className="sr-only">neutral site, vs.</span>
    </span>
  )
}

/**
 * Where a schedule game is played, in a fixed-width slot before the opponent (owner, #207):
 * "vs" at home, "at" away, the boxed "N" on a neutral field (#208; replacing #201–#203's line
 * under the name), so the opponents' names line up.
 */
export function SiteMark({ site }: { site: ScheduleGame["site"] }) {
  if (site === "neutral") return <NeutralTag className="w-5 shrink-0" />
  const m = MARK[site] ?? MARK.home
  return (
    <span className="w-5 shrink-0 text-muted-foreground">
      <span aria-hidden>{m.mark}</span>
      <span className="sr-only">{m.spoken}</span>
    </span>
  )
}
