import type { ScheduleGame } from "@/lib/api/types"

const MARK: Record<string, { mark: string; spoken: string; title?: string }> = {
  home: { mark: "vs", spoken: "vs." },
  away: { mark: "at", spoken: "at" },
  neutral: { mark: "N", spoken: "neutral site, vs.", title: "Neutral site" },
}

/**
 * Where a schedule game is played, in a fixed-width slot before the opponent (owner, #207):
 * "vs" at home, "at" away, a small boxed "N" on a neutral field (#208; replacing #201–#203's
 * line under the name), so the opponents' names line up. Screen readers hear "neutral site,
 * vs.".
 */
export function SiteMark({ site }: { site: ScheduleGame["site"] }) {
  const m = MARK[site] ?? MARK.home
  return (
    <span className="w-5 shrink-0 text-muted-foreground" title={m.title}>
      {/* A neutral field's N sits in a small outlined box, like the sport tags (owner). */}
      <span
        aria-hidden
        className={
          site === "neutral"
            ? "rounded-sm border border-border px-1 text-[0.625rem] leading-4 font-semibold"
            : undefined
        }
      >
        {m.mark}
      </span>
      <span className="sr-only">{m.spoken}</span>
    </span>
  )
}
