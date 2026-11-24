import { cn } from "@/lib/utils"

/** A sport's short name in a small outlined tag ("CFB"): search results, team headers (#199). */
export function SportTag({ label, className }: { label: string; className?: string }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-sm border border-border px-1 text-[0.625rem] leading-4 font-semibold tracking-wide text-foreground",
        className,
      )}
    >
      {label}
    </span>
  )
}
