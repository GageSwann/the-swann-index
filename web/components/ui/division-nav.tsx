import Link from "next/link"

import { DIVISION_NAME, type DivisionView } from "@/lib/divisions"
import { cn } from "@/lib/utils"

/**
 * FBS / FCS / All as links (each view is its own cached page, so the default FBS page
 * doesn't carry the other divisions' data). Shows the views listed in `hrefs`, in
 * FBS / FCS / All order. Styled like `Segmented`.
 */
export function DivisionNav<V extends DivisionView>({
  current,
  hrefs,
  label = "Division",
}: {
  current: V
  hrefs: Record<V, string>
  label?: string
}) {
  const views = (["fbs", "fcs", "all"] as const).filter((d): d is V => d in hrefs)
  return (
    <nav aria-label={label} className="inline-flex rounded-md border border-border bg-card p-0.5">
      {views.map((d) => (
        <Link
          key={d}
          href={hrefs[d]}
          aria-current={d === current ? "page" : undefined}
          className={cn(
            "rounded-sm px-3 py-1 text-sm font-medium",
            d === current
              ? "tsi-lit bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {d === "all" ? "All" : DIVISION_NAME[d]}
        </Link>
      ))}
    </nav>
  )
}
