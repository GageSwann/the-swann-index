import type { SnapshotView } from "@/lib/api/types"
import { formatDay } from "@/lib/format/time"
import { cn } from "@/lib/utils"

/**
 * Shown when TSI didn't publish this game at the time (before Oct 20, 2026, and the
 * Nov 10–19 outage) and the numbers were rebuilt later (decision #152): the forecast the
 * nightly run would have made that morning, from games played before it only.
 */
export function RebuiltNote({
  prediction: p,
  className,
}: {
  prediction: SnapshotView
  className?: string
}) {
  if (!p.rebuilt) return null
  return (
    <p className={cn("text-sm text-muted-foreground", className)}>
      <span className="font-semibold text-foreground">Rebuilt:</span> TSI didn&apos;t publish this
      game at the time. This is the forecast its morning run would have made on{" "}
      {formatDay(p.published_at)}, from games played before then.
    </p>
  )
}
