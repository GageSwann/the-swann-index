import type { ScheduleGame } from "@/lib/api/types"

const MARK: Record<string, { mark: string; spoken: string; title?: string }> = {
  home: { mark: "vs", spoken: "vs." },
  away: { mark: "at", spoken: "at" },
  neutral: { mark: "N", spoken: "neutral site, vs.", title: "Neutral site" },
}

/**
 * Where a schedule game is played, in a fixed-width slot before the opponent (owner, #207):
 * "vs" at home, "at" away, "N" on a neutral field (replacing #201–#203's line under the
 * name), so the opponents' names line up. Screen readers hear "neutral site, vs.".
 */
export function SiteMark({ site }: { site: ScheduleGame["site"] }) {
  const m = MARK[site] ?? MARK.home
  return (
    <span className="w-5 shrink-0 text-muted-foreground" title={m.title}>
      <span aria-hidden>{m.mark}</span>
      <span className="sr-only">{m.spoken}</span>
    </span>
  )
}
